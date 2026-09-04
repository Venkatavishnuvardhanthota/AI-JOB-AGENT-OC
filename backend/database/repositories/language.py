import uuid

from sqlalchemy import select

from database.models.language import Language
from database.repositories.base import BaseRepository


class LanguageRepository(BaseRepository):
    model_class = Language

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[Language]:
        stmt = select(Language).where(Language.profile_id == profile_id).order_by(Language.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_language(self, profile_id: uuid.UUID, language: str) -> bool:
        stmt = select(Language).where(
            Language.profile_id == profile_id,
            Language.language.ilike(language),
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none() is not None
