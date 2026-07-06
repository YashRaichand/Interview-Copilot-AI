from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import httpx
import uuid
import logging

from app.config import settings
from app.models import User
from app.schemas import UserRegister, TokenResponse
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

# bcrypt truncates at 72 bytes; passlib validates this strictly on hash.
# We explicitly truncate to 72 bytes ourselves so long passwords never 500.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BCRYPT_MAX_BYTES = 72


def _safe_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > BCRYPT_MAX_BYTES:
        encoded = encoded[:BCRYPT_MAX_BYTES]
    return encoded.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_safe_password(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(_safe_password(plain_password), hashed_password)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": user_id, "type": "access", "exp": expire, "iat": datetime.utcnow(), "jti": str(uuid.uuid4())}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "type": "refresh", "exp": expire, "iat": datetime.utcnow(), "jti": str(uuid.uuid4())}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(user_id: str) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: UserRegister) -> User:
        result = await self.db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            auth_provider="local",
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()
        logger.info(f"New user registered: {data.email}")
        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        await self.db.execute(update(User).where(User.id == user.id).values(last_login=datetime.utcnow()))
        return user

    async def get_or_create_google_user(self, google_user_data: Dict[str, Any]) -> User:
        google_id = google_user_data["sub"]
        email = google_user_data["email"]

        result = await self.db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()
        if user:
            await self.db.execute(update(User).where(User.id == user.id).values(last_login=datetime.utcnow()))
            return user

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            await self.db.execute(
                update(User).where(User.id == user.id).values(
                    google_id=google_id,
                    avatar_url=google_user_data.get("picture"),
                    is_verified=True,
                    last_login=datetime.utcnow(),
                )
            )
            return user

        user = User(
            email=email,
            full_name=google_user_data.get("name", email.split("@")[0]),
            google_id=google_id,
            avatar_url=google_user_data.get("picture"),
            auth_provider="google",
            is_verified=True,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def logout(self, token: str):
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            exp = payload.get("exp")
            if exp:
                ttl = int(exp - datetime.utcnow().timestamp())
                if ttl > 0:
                    await redis_client.setex(f"blacklist:{token}", ttl, "1")
        except Exception as e:
            logger.warning(f"Error blacklisting token: {e}")

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        from fastapi import HTTPException, status
        from jose import JWTError

        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id = payload.get("sub")
            token_type = payload.get("type")

            if not user_id or token_type != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

            is_blacklisted = await redis_client.get(f"blacklist:{refresh_token}")
            if is_blacklisted:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

            exp = payload.get("exp")
            if exp:
                ttl = int(exp - datetime.utcnow().timestamp())
                if ttl > 0:
                    await redis_client.setex(f"blacklist:{refresh_token}", ttl, "1")

            return create_token_pair(user_id)
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


async def exchange_google_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_response.json()
        if "error" in token_data:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google OAuth error: {token_data.get('error_description', token_data['error'])}",
            )
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        return user_response.json()
