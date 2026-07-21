from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import JobRepository
from app.services.audit import AuditService


class JobDiscoveryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = JobRepository(session)
        self.audit_service = AuditService(session)

    async def search(self, params: dict) -> dict:
        page = params.get("page", 1)
        page_size = params.get("page_size", 25)
        skip = (page - 1) * page_size

        jobs, total = await self.job_repo.search(
            search=params.get("search"),
            location=params.get("location"),
            employment_type=params.get("employment_type"),
            provider=params.get("provider"),
            skip=skip,
            limit=page_size,
        )

        return {
            "data": jobs,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            },
        }
