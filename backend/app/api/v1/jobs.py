import json
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.jobs.dependencies import get_job_discovery_service
from app.jobs.schemas import JobSearchRequest
from app.models import User
from app.repositories import BackgroundJobRepository, JobRepository
from app.schemas.job import JobResponse
from app.services.company_research import CompanyResearchService
from app.services.match_engine import MatchEngineService

router = APIRouter()


class JobUpdateRequest(BaseModel):
    is_active: bool | None = None
    viewed_at: str | None = None
    applied_at: str | None = None


# ── Fixed-path routes must come BEFORE /{job_id} ──


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


@router.get("/stats")
async def job_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = JobRepository(db)
    stmt_total = select(func.count()).select_from(repo.model_class)
    result = await db.execute(stmt_total)
    total = result.scalar() or 0

    stmt_by_source = select(repo.model_class.provider, func.count()).group_by(repo.model_class.provider)
    result = await db.execute(stmt_by_source)
    by_source = {row[0]: row[1] for row in result}

    return {
        "success": True,
        "data": {
            "total": total,
            "viewed": 0,
            "applied": 0,
            "active": total,
            "by_source": by_source,
        },
    }


@router.get("/saved")
async def saved_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories import ApplicationRepository

    app_repo = ApplicationRepository(db)
    apps, total = await app_repo.list_by_user(
        current_user.id, status=None, skip=(page - 1) * page_size, limit=page_size
    )
    items = []
    for a in apps:
        job = a.job
        if job:
            items.append({
                "id": str(job.id),
                "title": job.title,
                "company_name": job.company,
                "location": job.location,
                "source": job.provider,
                "salary_min": float(job.salary_min) if job.salary_min else None,
                "salary_max": float(job.salary_max) if job.salary_max else None,
                "salary_currency": job.currency,
                "job_type": job.employment_type,
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
            })
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "success": True, "items": items, "total": total,
        "page": page, "page_size": page_size, "total_pages": total_pages,
    }


@router.get("/recommended")
async def recommended_jobs(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = JobRepository(db)
    jobs, _ = await repo.search(skip=0, limit=10)
    return {"success": True, "data": [{"job_id": str(j.id), "title": j.title, "company": j.company} for j in jobs]}


@router.get("/search")
async def search_jobs(
    query: str | None = Query(None, alias="search"),
    location: str | None = Query(None),
    employment_type: str | None = Query(None),
    provider: str | None = Query(None),
    sources: str | None = Query(None),
    remote_only: bool | None = Query(None),
    salary_min: float | None = Query(None),
    salary_max: float | None = Query(None),
    job_type: str | None = Query(None),
    skills: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    discovery = get_job_discovery_service()
    offset = (page - 1) * page_size

    providers_list = None
    if provider:
        providers_list = [provider]
    elif sources:
        providers_list = [s.strip() for s in sources.split(",") if s.strip()]

    req = JobSearchRequest(
        query=query or "",
        location=location,
        remote_only=remote_only or None,
        employment_type=job_type or employment_type,
        salary_min=salary_min,
        salary_max=salary_max,
        providers=providers_list,
        limit=page_size,
        offset=offset,
    )

    result = await discovery.search(req)

    items = []
    for job in result.results:
        loc_parts = []
        if job.location.city:
            loc_parts.append(job.location.city)
        if job.location.state:
            loc_parts.append(job.location.state)
        if job.location.country:
            loc_parts.append(job.location.country)
        if job.location.remote_type and job.location.remote_type.value == "remote":
            loc_parts.append("Remote")

        items.append({
            "id": str(job.id),
            "title": job.title,
            "company_name": job.company.name,
            "location": ", ".join(loc_parts) if loc_parts else None,
            "remote": job.location.remote_type and job.location.remote_type.value == "remote",
            "salary_min": float(job.salary.min_amount) if job.salary else None,
            "salary_max": float(job.salary.max_amount) if job.salary else None,
            "salary_currency": job.salary.currency if job.salary else None,
            "salary_period": job.salary.period if job.salary else None,
            "posted_at": job.posted_date.isoformat() if job.posted_date else None,
            "source": job.provider,
            "job_type": job.employment_type.value if job.employment_type else None,
            "skills": job.skills or [],
            "description": job.description,
        })

    total = result.metadata.total_results
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "success": True,
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/refresh")
async def refresh_jobs(
    body: dict | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = BackgroundJobRepository(db)
    job = repo.model_class(
        user_id=current_user.id,
        job_type="job_refresh",
        status="pending",
        payload=json.dumps(body) if body else "{}",
    )
    created = await repo.create(job)
    return {
        "success": True,
        "data": {
            "task_id": str(created.id),
            "status": created.status,
            "error": created.error_message,
            "created_at": created.created_at.isoformat() if created.created_at else None,
            "completed_at": created.completed_at.isoformat() if created.completed_at else None,
        },
    }


@router.get("/refresh/status/{task_id}")
async def refresh_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = BackgroundJobRepository(db)
    job = await repo.get_by_id(uuid.UUID(task_id))
    if not job:
        raise NotFoundError("Task not found.")
    return {
        "success": True,
        "data": {
            "task_id": str(job.id),
            "status": job.status,
            "error": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        },
    }


@router.get("/")
@router.get("")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    source: str | None = Query(None),
    active_only: bool | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = JobRepository(db)
    jobs, total = await repo.search(
        provider=source,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    items = []
    for job in jobs:
        items.append({
            "id": str(job.id),
            "title": job.title,
            "company_name": job.company,
            "location": job.location,
            "source": job.provider,
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
            "salary_currency": job.currency,
            "job_type": job.employment_type,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
            "description": job.description,
        })
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        "success": True, "items": items, "total": total,
        "page": page, "page_size": page_size, "total_pages": total_pages,
    }


# ── Parameterized routes ──


@router.get("/{job_id}")
async def get_job(job_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = JobRepository(db)
    job = await repo.get_by_id(uuid.UUID(job_id))
    if not job:
        raise NotFoundError("Job not found.")
    return {"success": True, "data": JobResponse.model_validate(job).model_dump()}


@router.patch("/{job_id}")
async def update_job(
    job_id: str,
    body: JobUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = JobRepository(db)
    job = await repo.get_by_id(uuid.UUID(job_id))
    if not job:
        raise NotFoundError("Job not found.")
    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(job, key, value)
    await repo.update(job)
    return {"success": True, "data": {"id": str(job.id)}}


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
