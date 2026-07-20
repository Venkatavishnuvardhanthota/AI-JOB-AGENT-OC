import uuid

from sqlalchemy import select

from app.models.company_insight import CompanyInsight
from app.repositories.base import BaseRepository


class CompanyInsightRepository(BaseRepository):
    model_class = CompanyInsight

    async def get_by_job(self, job_id: uuid.UUID) -> CompanyInsight | None:
        stmt = select(CompanyInsight).where(CompanyInsight.job_id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
