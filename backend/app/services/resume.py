import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.resume_version import ResumeVersion
from app.repositories.career_profile import CareerProfileRepository
from app.repositories.resume import ResumeRepository
from app.services.audit import AuditService


class ResumeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resume_repo = ResumeRepository(session)
        self.profile_repo = CareerProfileRepository(session)
        self.audit_service = AuditService(session)

    async def list_resumes(self, user_id: uuid.UUID, archived: bool | None = None) -> list[ResumeVersion]:
        return await self.resume_repo.list_versions(user_id, archived=archived)

    async def get_resume(self, resume_id: uuid.UUID) -> ResumeVersion:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise NotFoundError("Resume not found.")
        return resume

    async def generate_resume(
        self, user_id: uuid.UUID, job_id: uuid.UUID | None, template: str, title: str | None
    ) -> ResumeVersion:
        latest_version = await self.resume_repo.latest_version(user_id)
        resume = ResumeVersion(
            user_id=user_id,
            version=latest_version + 1,
            title=title or f"Resume v{latest_version + 1}",
            template=template,
            generated_for_job_id=job_id,
        )
        created = await self.resume_repo.create(resume)
        await self.audit_service.log(
            "RESUME_GENERATED",
            user_id=user_id,
            entity="resume",
            entity_id=created.id,
            outcome="success",
        )
        return created

    async def archive_resume(self, resume_id: uuid.UUID) -> ResumeVersion:
        resume = await self.resume_repo.archive(resume_id)
        if not resume:
            raise NotFoundError("Resume not found.")
        return resume

    async def restore_resume(self, resume_id: uuid.UUID) -> ResumeVersion:
        resume = await self.resume_repo.restore(resume_id)
        if not resume:
            raise NotFoundError("Resume not found.")
        return resume
