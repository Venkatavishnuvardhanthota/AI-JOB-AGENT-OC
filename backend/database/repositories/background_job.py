import uuid

from sqlalchemy import select

from database.models.background_job import BackgroundJob
from database.repositories.base import BaseRepository


class BackgroundJobRepository(BaseRepository):
    model_class = BackgroundJob

    async def list_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> list[BackgroundJob]:
        stmt = (
            select(BackgroundJob)
            .where(BackgroundJob.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(BackgroundJob.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending(self, limit: int = 10) -> list[BackgroundJob]:
        stmt = (
            select(BackgroundJob)
            .where(BackgroundJob.status == "pending")
            .limit(limit)
            .order_by(BackgroundJob.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
