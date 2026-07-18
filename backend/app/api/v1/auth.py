from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_refresh_token_repository,
    get_user_repository,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: RegisterRequest,
    repo: UserRepository = Depends(get_user_repository),
) -> User:
    existing = await repo.get_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    user = await repo.create(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    repo: UserRepository = Depends(get_user_repository),
    refresh_repo: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
) -> dict[str, str]:
    user = await repo.get_by_email(request.email)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=30),
    )
    refresh_token_value = create_refresh_token()
    await refresh_repo.create(
        token=refresh_token_value,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    refresh_repo: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
) -> dict[str, str]:
    stored = await refresh_repo.get_by_token(request.refresh_token)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )
    if stored.is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
        )
    expires_at = stored.expires_at
    if expires_at.tzinfo is None:
        from datetime import timezone as tz
        expires_at = expires_at.replace(tzinfo=tz.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
        )
    stored.is_revoked = True
    stored.revoked_at = datetime.now(timezone.utc)
    await refresh_repo.session.flush()

    new_access_token = create_access_token(subject=str(stored.user_id))
    new_refresh_token_value = create_refresh_token()
    await refresh_repo.create(
        token=new_refresh_token_value,
        user_id=stored.user_id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token_value,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=204)
async def logout(
    request: LogoutRequest,
    refresh_repo: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
) -> None:
    stored = await refresh_repo.get_by_token(request.refresh_token)
    if stored and not stored.is_revoked:
        stored.is_revoked = True
        stored.revoked_at = datetime.now(timezone.utc)
        await refresh_repo.session.flush()


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
