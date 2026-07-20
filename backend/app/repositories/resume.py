import uuid

from sqlalchemy import func, select

from app.models.resume_version import ResumeVersion
from app.repositories.base import BaseRepository


class ResumeRepository(BaseRepository):
    model_class = ResumeVersion

    async def list_versions(self, user_id: uuid.UUID, archived: bool | None = None) -> list[ResumeVersion]:
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
        resume = await self.get_by_id(resume_id)
        if resume:
            resume.archived = True
            await self.session.flush()
        return resume

    async def restore(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        resume = await self.get_by_id(resume_id)
        if resume:
            resume.archived = False
            await self.session.flush()
        return resume
