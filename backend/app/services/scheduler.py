import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduler_job import SchedulerJob
from app.repositories.scheduler import SchedulerRepository
from app.services.audit import AuditService


class SchedulerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SchedulerRepository(session)
        self.audit_service = AuditService(session)

    async def list_jobs(self, user_id: uuid.UUID) -> list[SchedulerJob]:
        return await self.repo.list_by_user(user_id)

    async def create_job(self, user_id: uuid.UUID, name: str, schedule: str) -> SchedulerJob:
        job = SchedulerJob(
            user_id=user_id,
            name=name,
            schedule=schedule,
        )
        created = await self.repo.create(job)
        await self.audit_service.log(
            "SCHEDULER_JOB_CREATED",
            user_id=user_id,
            entity="scheduler_job",
            entity_id=created.id,
            outcome="success",
        )
        return created

    async def toggle(self, job_id: uuid.UUID) -> SchedulerJob:
        job = await self.repo.get_by_id(job_id)
        if job:
            job.enabled = not job.enabled
            await self.repo.update(job)
        return job
