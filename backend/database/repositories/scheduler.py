import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from database.models.scheduler_job import SchedulerJob
from database.repositories.base import BaseRepository


class SchedulerRepository(BaseRepository):
    model_class = SchedulerJob

    async def list_by_user(self, user_id: uuid.UUID) -> list[SchedulerJob]:
        stmt = select(SchedulerJob).where(SchedulerJob.user_id == user_id).order_by(SchedulerJob.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def next_jobs(self, limit: int = 10) -> list[SchedulerJob]:
        stmt = (
            select(SchedulerJob)
            .where(SchedulerJob.enabled.is_(True))
            .where(SchedulerJob.next_run <= datetime.now(timezone.utc))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
