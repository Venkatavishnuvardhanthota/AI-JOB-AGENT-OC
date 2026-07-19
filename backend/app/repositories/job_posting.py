import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.job_posting import JobPosting
from app.repositories.base import BaseRepository


class JobPostingRepository(BaseRepository[JobPosting]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(JobPosting, session)

    async def search(
        self,
        *,
        query: str = "",
        location: str | None = None,
        remote_only: bool = False,
        sources: list[str] | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        job_type: str | None = None,
        skills: list[str] | None = None,
        is_active: bool | None = None,
        user_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by_desc: str | None = "posted_at",
    ) -> tuple[Sequence[JobPosting], int]:
        filters: list = []

        if query:
            q = f"%{query}%"
            filters.append(
                or_(
                    self.model.title.ilike(q),
                    self.model.company_name.ilike(q),
                    self.model.description.ilike(q),
                    self.model.skills.any(query, type_=String),
                    self.model.location.ilike(q),
                )
            )

        if location:
            loc_filter = f"%{location}%"
            filters.append(self.model.location.ilike(loc_filter))

        if remote_only:
            filters.append(self.model.remote.is_(True))

        if sources:
            filters.append(self.model.source.in_(sources))

        if salary_min is not None:
            filters.append(
                or_(
                    self.model.salary_max >= salary_min,
                    and_(
                        self.model.salary_min.is_(None),
                        self.model.salary_max.is_(None),
                    ),
                )
            )

        if salary_max is not None:
            filters.append(self.model.salary_min <= salary_max)

        if job_type:
            filters.append(self.model.job_type.ilike(f"%{job_type}%"))

        if skills:
            for skill in skills:
                filters.append(self.model.skills.any(skill, type_=String))

        if is_active is not None:
            filters.append(self.model.is_active == is_active)

        if user_id is not None:
            filters.append(self.model.user_id == user_id)

        base_query: Select = select(self.model)
        count_query: Select = select(func.count()).select_from(self.model)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        if order_by_desc:
            col = getattr(self.model, order_by_desc, None)
            if col is not None:
                base_query = base_query.order_by(col.desc().nullslast())
            else:
                base_query = base_query.order_by(self.model.posted_at.desc().nullslast())
        else:
            base_query = base_query.order_by(self.model.posted_at.desc().nullslast())

        base_query = base_query.offset(skip).limit(limit)
        result = await self.session.execute(base_query)
        items = result.scalars().all()

        return items, total

    async def bulk_create(self, jobs: list[dict]) -> list[JobPosting]:
        instances: list[JobPosting] = []
        for data in jobs:
            instance = self.model(**data)
            self.session.add(instance)
            instances.append(instance)
        await self.session.flush()
        for inst in instances:
            await self.session.refresh(inst)
        return instances

    async def get_by_hash(self, content_hash: str) -> JobPosting | None:
        stmt = select(self.model).where(self.model.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_source_and_id(self, source: str, source_job_id: str) -> JobPosting | None:
        stmt = select(self.model).where(
            and_(self.model.source == source, self.model.source_job_id == source_job_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_saved(
        self,
        user_id: uuid.UUID,
        *,
        viewed: bool | None = None,
        applied: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[JobPosting], int]:
        filters = [self.model.user_id == user_id]
        if viewed is True:
            filters.append(self.model.viewed_at.isnot(None))
        elif viewed is False:
            filters.append(self.model.viewed_at.is_(None))
        if applied is True:
            filters.append(self.model.applied_at.isnot(None))
        elif applied is False:
            filters.append(self.model.applied_at.is_(None))

        return await self.list(
            filters=filters, skip=skip, limit=limit,
            order_by=self.model.posted_at.desc().nullslast(),
        )

    async def mark_viewed(self, job_id: uuid.UUID) -> JobPosting | None:
        return await self.update(job_id, viewed_at=datetime.utcnow())

    async def mark_applied(self, job_id: uuid.UUID) -> JobPosting | None:
        return await self.update(job_id, applied_at=datetime.utcnow())

    async def get_stats(self, user_id: uuid.UUID | None = None) -> dict:
        filters: list = []
        if user_id:
            filters.append(self.model.user_id == user_id)

        base_filter = and_(*filters) if filters else True

        total_stmt = select(func.count()).select_from(self.model).where(base_filter)
        total = (await self.session.execute(total_stmt)).scalar_one()

        viewed_stmt = select(func.count()).select_from(self.model).where(
            and_(self.model.viewed_at.isnot(None), base_filter)
        )
        viewed = (await self.session.execute(viewed_stmt)).scalar_one()

        applied_stmt = select(func.count()).select_from(self.model).where(
            and_(self.model.applied_at.isnot(None), base_filter)
        )
        applied = (await self.session.execute(applied_stmt)).scalar_one()

        active_stmt = select(func.count()).select_from(self.model).where(
            and_(self.model.is_active.is_(True), base_filter)
        )
        active = (await self.session.execute(active_stmt)).scalar_one()

        source_stmt = select(self.model.source, func.count()).where(base_filter).group_by(self.model.source)
        source_result = await self.session.execute(source_stmt)
        by_source = {row[0]: row[1] for row in source_result.fetchall()}

        return {
            "total": total,
            "viewed": viewed,
            "applied": applied,
            "active": active,
            "by_source": by_source,
        }
