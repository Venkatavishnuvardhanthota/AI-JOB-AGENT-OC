import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.job import JobRepository
from app.schemas.job import JobResponse
from app.services.company_research import CompanyResearchService
from app.services.job_discovery import JobDiscoveryService
from app.services.match_engine import MatchEngineService

router = APIRouter()


@router.get("/search")
async def search_jobs(
    search: str | None = Query(None),
    location: str | None = Query(None),
    employment_type: str | None = Query(None),
    provider: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = JobDiscoveryService(db)
    params = {
        "search": search,
        "location": location,
        "employment_type": employment_type,
        "provider": provider,
        "page": page,
        "page_size": page_size,
    }
    result = await service.search(params)
    return {"success": True, **result}


@router.get("/recommended")
async def recommended_jobs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = JobRepository(db)
    jobs, _ = await repo.search(skip=0, limit=10)
    return {"success": True, "data": [{"job_id": str(j.id), "title": j.title, "company": j.company} for j in jobs]}


@router.get("/{job_id}")
async def get_job(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = JobRepository(db)
    job = await repo.get_by_id(uuid.UUID(job_id))
    if not job:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Job not found.")
    return {"success": True, "data": JobResponse.model_validate(job).model_dump()}


@router.get("/{job_id}/match")
async def job_match(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = MatchEngineService(db)
    result = await service.calculate_score(current_user.id, uuid.UUID(job_id))
    return {"success": True, "data": result}


@router.get("/{job_id}/company")
async def job_company(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CompanyResearchService(db)
    result = await service.research(uuid.UUID(job_id))
    return {"success": True, "data": result}


@router.get("/providers")
async def list_providers():
    providers = [
        {"name": "LinkedIn", "status": "enabled"},
        {"name": "Greenhouse", "status": "enabled"},
        {"name": "Lever", "status": "enabled"},
        {"name": "Ashby", "status": "enabled"},
        {"name": "Wellfound", "status": "enabled"},
        {"name": "Workday", "status": "enabled"},
    ]
    return {"success": True, "data": providers}
