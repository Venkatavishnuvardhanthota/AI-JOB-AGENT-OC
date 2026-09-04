import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import decode_access_token
from app.models import User
from app.repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise AuthenticationError("Invalid or expired token.")
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise AuthenticationError("Invalid token payload.")
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid user identifier in token.")
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise NotFoundError("User not found.")
    if not user.is_active:
        raise AuthorizationError("Inactive user account.")
    return user
