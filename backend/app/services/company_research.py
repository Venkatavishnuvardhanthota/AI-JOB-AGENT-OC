import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.company_insight import CompanyInsightRepository
from app.repositories.job import JobRepository
from app.services.audit import AuditService


class CompanyResearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = JobRepository(session)
        self.insight_repo = CompanyInsightRepository(session)
        self.audit_service = AuditService(session)

    async def research(self, job_id: uuid.UUID) -> dict:
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found.")

        insight = await self.insight_repo.get_by_job(job_id)
        if insight:
            return {
                "company": job.company,
                "industry": insight.industry,
                "size": insight.company_size,
                "summary": insight.summary,
                "culture": insight.culture,
                "headquarters": insight.headquarters,
            }

        return {
            "company": job.company,
            "industry": None,
            "size": None,
            "summary": None,
            "culture": None,
            "headquarters": job.location,
        }
