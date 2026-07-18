from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)

    async def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_user_tokens(self, user_id: str) -> None:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False),
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        now = datetime.now(timezone.utc)
        for token in tokens:
            token.is_revoked = True
            token.revoked_at = now
        await self.session.flush()

    async def cleanup_expired(self) -> int:
        stmt = select(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        for token in tokens:
            await self.session.delete(token)
        await self.session.flush()
        return len(tokens)
