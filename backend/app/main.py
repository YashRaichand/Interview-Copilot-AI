from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
import uuid

from app.config import settings
from app.database import create_tables
from app.utils.redis_client import redis_client
from app.utils.logger import setup_logging
from app.api.v1.router import api_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    await redis_client.connect()

    if settings.ENVIRONMENT in ("development", "testing"):
        try:
            await create_tables()
            logger.info("Database tables verified")
        except Exception as e:
            logger.warning(f"Could not create tables: {e}")

    try:
        from app.nlp.semantic_matcher import semantic_matcher
        await semantic_matcher.load_model()
        logger.info("Sentence transformer model loaded")
    except Exception as e:
        logger.warning(f"Could not preload semantic matcher: {e}")

    logger.info("Application startup complete")
    yield

    await redis_client.disconnect()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered interview preparation platform: resume parsing, ATS scoring, AI mock interviews, and personalized roadmaps.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    request.state.request_id = request_id

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

    logger.info(f"{request.method} {request.url.path} status={response.status_code} time={process_time:.2f}ms request_id={request_id}")
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(e) for e in error["loc"])
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"error": "Validation failed", "detail": errors, "status_code": 422})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc) if settings.DEBUG else "An unexpected error occurred", "status_code": 500},
    )


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check():
    checks = {"api": "healthy", "redis": "unknown", "database": "unknown"}

    redis_ok = await redis_client.ping()
    checks["redis"] = "healthy" if redis_ok else "degraded"

    try:
        from app.database import engine
        import sqlalchemy
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks, "version": settings.APP_VERSION}


if settings.PROMETHEUS_ENABLED:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator(should_group_status_codes=True, should_ignore_untemplated=True, excluded_handlers=["/health", "/metrics"]).instrument(app).expose(app)
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError:
        logger.warning("prometheus-fastapi-instrumentator not installed, metrics disabled")
