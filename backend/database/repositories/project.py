import uuid

from sqlalchemy import select

from database.models.project import Project
from database.repositories.base import BaseRepository


class ProjectRepository(BaseRepository):
    model_class = Project

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[Project]:
        stmt = select(Project).where(Project.profile_id == profile_id).order_by(Project.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_by_name(self, profile_id: uuid.UUID, name: str) -> bool:
        stmt = select(Project).where(Project.profile_id == profile_id, Project.name == name)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none() is not None
