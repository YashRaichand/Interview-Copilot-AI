from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router
from app.api.v1.routes import jd_router, analysis_router, interview_router, roadmap_router, reports_router, dashboard_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(resume_router)
api_router.include_router(jd_router)
api_router.include_router(analysis_router)
api_router.include_router(interview_router)
api_router.include_router(roadmap_router)
api_router.include_router(reports_router)
api_router.include_router(dashboard_router)
