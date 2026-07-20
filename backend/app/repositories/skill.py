import uuid

from sqlalchemy import select

from app.models.skill import Skill
from app.repositories.base import BaseRepository


class SkillRepository(BaseRepository):
    model_class = Skill

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[Skill]:
        stmt = select(Skill).where(Skill.profile_id == profile_id).order_by(Skill.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists(self, profile_id: uuid.UUID, name: str) -> bool:
        stmt = select(Skill).where(Skill.profile_id == profile_id, Skill.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
