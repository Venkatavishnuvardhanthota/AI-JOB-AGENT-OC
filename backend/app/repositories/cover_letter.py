import uuid

from sqlalchemy import select

from app.models.cover_letter import CoverLetter
from app.repositories.base import BaseRepository


class CoverLetterRepository(BaseRepository):
    model_class = CoverLetter

    async def list_by_user(self, user_id: uuid.UUID) -> list[CoverLetter]:
        stmt = select(CoverLetter).where(CoverLetter.user_id == user_id).order_by(CoverLetter.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
