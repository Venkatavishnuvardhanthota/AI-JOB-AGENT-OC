import uuid

from sqlalchemy import func, select

from database.models.resume_version import ResumeVersion
from database.repositories.base import BaseRepository


class ResumeVersionRepository(BaseRepository):
    model_class = ResumeVersion

    async def list_by_user(self, user_id: uuid.UUID, archived: bool | None = None) -> list[ResumeVersion]:
        stmt = select(ResumeVersion).where(ResumeVersion.user_id == user_id)
        if archived is not None:
            stmt = stmt.where(ResumeVersion.archived == archived)
        stmt = stmt.order_by(ResumeVersion.version.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def latest_version(self, user_id: uuid.UUID) -> int:
        stmt = select(func.max(ResumeVersion.version)).where(ResumeVersion.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def archive(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        return await self.update_fields(resume_id, archived=True)

    async def restore(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        return await self.update_fields(resume_id, archived=False)
