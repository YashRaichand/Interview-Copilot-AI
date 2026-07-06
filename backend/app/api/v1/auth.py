from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode

from app.database import get_db
from app.schemas import UserRegister, UserLogin, TokenResponse, RefreshTokenRequest, GoogleAuthRequest, UserResponse, MessageResponse
from app.services.auth_service import AuthService, create_token_pair, exchange_google_code
from app.dependencies import get_current_user, strict_rate_limiter
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db), _=Depends(strict_rate_limiter)):
    service = AuthService(db)
    user = await service.register(data)
    await db.commit()
    return create_token_pair(str(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db), _=Depends(strict_rate_limiter)):
    service = AuthService(db)
    user = await service.authenticate(data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    await db.commit()
    return create_token_pair(str(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh_tokens(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.logout(credentials.credentials)
    return MessageResponse(message="Successfully logged out")


@router.post("/google", response_model=TokenResponse)
async def google_oauth(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db), _=Depends(strict_rate_limiter)):
    google_user = await exchange_google_code(data.code, data.redirect_uri)
    service = AuthService(db)
    user = await service.get_or_create_google_user(google_user)
    await db.commit()
    return create_token_pair(str(user.id))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/google/url")
async def get_google_auth_url():
    from app.config import settings
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID, "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code", "scope": "openid email profile", "access_type": "offline", "prompt": "select_account",
    }
    return {"url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)}
