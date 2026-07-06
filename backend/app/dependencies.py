from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
import uuid

from app.database import get_db
from app.config import settings
from app.models import User
from app.utils.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """
    Get the real client IP. Behind Render's (or any) reverse proxy,
    request.client can be None and the proxy's own IP is what's exposed
    directly, so we prefer the X-Forwarded-For header when present.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    is_blacklisted = await redis_client.get(f"blacklist:{token}")
    if is_blacklisted:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst = burst

    async def __call__(self, request: Request):
        client_ip = get_client_ip(request)
        key = f"rate_limit:{client_ip}:{request.url.path}"

        try:
            current = await redis_client.get(key)

            if current is None:
                await redis_client.setex(key, 60, "1")
            elif int(current) >= self.requests_per_minute + self.burst:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60"},
                )
            else:
                await redis_client.incr(key)
        except HTTPException:
            raise
        except Exception as e:
            # Never let rate limiting itself break the request (e.g. Redis hiccup)
            logger.warning(f"Rate limiter error (allowing request through): {e}")


rate_limiter = RateLimiter(
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    burst=settings.RATE_LIMIT_BURST,
)

strict_rate_limiter = RateLimiter(requests_per_minute=10, burst=5)
