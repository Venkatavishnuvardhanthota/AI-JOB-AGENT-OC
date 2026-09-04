import uuid

from sqlalchemy import select

from database.models.achievement import Achievement
from database.repositories.base import BaseRepository


class AchievementRepository(BaseRepository):
    model_class = Achievement

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[Achievement]:
        stmt = (
            select(Achievement)
            .where(Achievement.profile_id == profile_id)
            .order_by(Achievement.display_order.asc().nullslast(), Achievement.date.desc().nullslast(), Achievement.title)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_title(self, profile_id: uuid.UUID, title: str) -> bool:
        stmt = select(Achievement).where(
            Achievement.profile_id == profile_id,
            Achievement.title.ilike(title),
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none() is not None
