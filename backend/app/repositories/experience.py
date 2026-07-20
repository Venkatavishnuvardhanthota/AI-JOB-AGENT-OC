import uuid

from sqlalchemy import select

from app.models.experience import Experience
from app.repositories.base import BaseRepository


class ExperienceRepository(BaseRepository):
    model_class = Experience

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[Experience]:
        stmt = select(Experience).where(Experience.profile_id == profile_id).order_by(Experience.start_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
