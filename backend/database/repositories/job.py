from sqlalchemy import func, or_, select

from database.models.job import Job
from database.repositories.base import BaseRepository


class JobRepository(BaseRepository):
    model_class = Job

    async def search(
        self,
        search: str | None = None,
        location: str | None = None,
        employment_type: str | None = None,
        provider: str | None = None,
        skip: int = 0,
        limit: int = 25,
    ) -> tuple[list[Job], int]:
        stmt = select(Job)
        count_stmt = select(func.count()).select_from(Job)

        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(Job.title.ilike(like), Job.company.ilike(like), Job.description.ilike(like)))
            count_stmt = count_stmt.where(
                or_(Job.title.ilike(like), Job.company.ilike(like), Job.description.ilike(like))
            )
        if location:
            stmt = stmt.where(Job.location.ilike(f"%{location}%"))
            count_stmt = count_stmt.where(Job.location.ilike(f"%{location}%"))
        if employment_type:
            stmt = stmt.where(Job.employment_type == employment_type)
            count_stmt = count_stmt.where(Job.employment_type == employment_type)
        if provider:
            stmt = stmt.where(Job.provider == provider)
            count_stmt = count_stmt.where(Job.provider == provider)

        stmt = stmt.offset(skip).limit(limit).order_by(Job.created_at.desc())
        result = await self.session.execute(stmt)
        jobs = list(result.unique().scalars().all())

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        return jobs, total

    async def find_duplicates(self, provider: str, provider_job_id: str) -> Job | None:
        stmt = select(Job).where(Job.provider == provider, Job.provider_job_id == provider_job_id)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def bulk_create(self, jobs: list[Job]) -> list[Job]:
        self.session.add_all(jobs)
        await self.session.flush()
        for j in jobs:
            await self.session.refresh(j)
        return jobs
