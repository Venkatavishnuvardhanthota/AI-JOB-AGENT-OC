import uuid

from sqlalchemy import select

from database.models.job_search import JobSearch
from database.repositories.base import BaseRepository


class JobSearchRepository(BaseRepository):
    model_class = JobSearch

    async def list_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> list[JobSearch]:
        stmt = (
            select(JobSearch)
            .where(JobSearch.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(JobSearch.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
