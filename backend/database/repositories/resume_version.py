import uuid

from sqlalchemy import func, select
from sqlalchemy import update as sa_update

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

    async def list_by_user_with_sections(self, user_id: uuid.UUID) -> list[ResumeVersion]:
        from sqlalchemy.orm import joinedload

        stmt = (
            select(ResumeVersion)
            .options(joinedload(ResumeVersion.sections))
            .where(ResumeVersion.user_id == user_id)
            .order_by(ResumeVersion.version.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_by_user_and_origin(self, user_id: uuid.UUID, origin: str) -> list[ResumeVersion]:
        stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.user_id == user_id, ResumeVersion.origin == origin)
            .order_by(ResumeVersion.version.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_master_resumes_with_sections(self, user_id: uuid.UUID) -> list[ResumeVersion]:
        from sqlalchemy.orm import joinedload

        stmt = (
            select(ResumeVersion)
            .options(joinedload(ResumeVersion.sections))
            .where(
                ResumeVersion.user_id == user_id,
                ResumeVersion.origin == "master",
                ResumeVersion.archived.is_(False),
            )
            .order_by(ResumeVersion.version.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_generated_for_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> ResumeVersion | None:
        stmt = (
            select(ResumeVersion)
            .where(
                ResumeVersion.user_id == user_id,
                ResumeVersion.origin == "generated",
                ResumeVersion.generated_for_job_id == job_id,
                ResumeVersion.archived.is_(False),
            )
            .order_by(ResumeVersion.version.desc())
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_with_sections(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        from sqlalchemy.orm import joinedload

        stmt = (
            select(ResumeVersion)
            .options(joinedload(ResumeVersion.sections))
            .where(ResumeVersion.id == resume_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def latest_version(self, user_id: uuid.UUID) -> int:
        stmt = select(func.max(ResumeVersion.version)).where(ResumeVersion.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def archive(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        return await self.update_fields(resume_id, archived=True)

    async def restore(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        return await self.update_fields(resume_id, archived=False)

    async def set_default(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion | None:
        stmt = (
            sa_update(ResumeVersion)
            .where(ResumeVersion.user_id == user_id)
            .values(is_default=False)
        )
        await self.session.execute(stmt)
        return await self.update_fields(resume_id, is_default=True)

    async def get_default(self, user_id: uuid.UUID) -> ResumeVersion | None:
        stmt = select(ResumeVersion).where(
            ResumeVersion.user_id == user_id, ResumeVersion.is_default.is_(True)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def unset_default(self, user_id: uuid.UUID) -> None:
        stmt = (
            sa_update(ResumeVersion)
            .where(ResumeVersion.user_id == user_id, ResumeVersion.is_default.is_(True))
            .values(is_default=False)
        )
        await self.session.execute(stmt)
