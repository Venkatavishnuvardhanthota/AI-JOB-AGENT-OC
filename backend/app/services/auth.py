import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.services.audit import AuditService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.refresh_token_repo = RefreshTokenRepository(session)
        self.audit_service = AuditService(session)

    async def register(self, email: str, password: str, first_name: str, last_name: str) -> dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError("Email already exists.")

        user = User(
            email=email,
            password_hash=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
        )
        created = await self.user_repo.create(user)
        await self.audit_service.log("REGISTRATION", user_id=created.id, outcome="success")
        return {"user_id": str(created.id), "email": created.email}

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            await self.audit_service.log("LOGIN_FAILURE", outcome="failed")
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("Account is inactive.")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token()
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        from app.models.refresh_token import RefreshToken

        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.refresh_token_repo.create(rt)
        await self.audit_service.log("LOGIN_SUCCESS", user_id=user.id, outcome="success")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.access_token_expire_seconds,
            "token_type": "Bearer",
        }

    async def logout(self, user_id: uuid.UUID) -> None:
        await self.refresh_token_repo.revoke_all_for_user(user_id)
        await self.audit_service.log("LOGOUT", user_id=user_id, outcome="success")

    async def refresh_token(self, refresh_token: str) -> dict:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        stored = await self.refresh_token_repo.get_by_token_hash(token_hash)
        if not stored:
            raise AuthenticationError("Invalid or expired refresh token.")

        access_token = create_access_token(subject=str(stored.user_id))
        return {"access_token": access_token, "expires_in": settings.access_token_expire_seconds}

    async def change_password(self, user_id: uuid.UUID, current_password: str, new_password: str) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user or not verify_password(current_password, user.password_hash):
            raise ValidationError("Current password is incorrect.")

        user.password_hash = get_password_hash(new_password)
        await self.user_repo.update(user)
        await self.refresh_token_repo.revoke_all_for_user(user_id)
        await self.audit_service.log("PASSWORD_CHANGE", user_id=user_id, outcome="success")

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    async def delete_account(self, user_id: uuid.UUID) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        user.is_active = False
        user.deleted_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)
        await self.refresh_token_repo.revoke_all_for_user(user_id)
        await self.audit_service.log("ACCOUNT_DELETION", user_id=user_id, outcome="success")
