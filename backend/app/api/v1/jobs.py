import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.job import JobResponse, JobSearchRequest, JobSearchResponse, JobSearchResult, JobUpdate
from app.services.job_queue import get_job_queue
from app.services.job_scheduler import ScheduleInterval, get_job_scheduler
from app.services.job_search import JobSearchService

router = APIRouter()


def get_job_search_service(
    db: AsyncSession = Depends(get_db),
) -> JobSearchService:
    return JobSearchService(session=db)


@router.post("/search", response_model=JobSearchResult)
async def search_jobs(
    search_req: JobSearchRequest,
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Search across all enabled providers and store new jobs."""
    return await service.search_and_store(search_req, user_id=current_user.id)


@router.post("/search/async")
async def search_jobs_async(
    search_req: JobSearchRequest,
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
    db: AsyncSession = Depends(get_db),
):
    """Enqueue a background job search."""
    queue = get_job_queue()

    async def _background_search():
        async with db as session:
            svc = JobSearchService(session=session)
            return await svc.search_and_store(search_req, user_id=current_user.id)

    task_id = await queue.enqueue(
        f"search:{current_user.email}:{search_req.query}",
        _background_search,
    )
    return {"task_id": task_id, "status": "pending"}


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the status of an async search task."""
    queue = get_job_queue()
    task = queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": task.id,
        "status": task.status.value,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.get("", response_model=JobSearchResponse)
async def list_jobs(
    query: str = Query(default="", max_length=500),
    location: str | None = None,
    remote_only: bool = False,
    sources: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    job_type: str | None = None,
    skills: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """List stored jobs with filtering and pagination."""
    source_list = sources.split(",") if sources else None
    skills_list = skills.split(",") if skills else None

    items, total = await service.list_jobs(
        query=query,
        location=location,
        remote_only=remote_only,
        sources=source_list,
        salary_min=salary_min,
        salary_max=salary_max,
        job_type=job_type,
        skills=skills_list,
        is_active=is_active,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    return JobSearchResponse(
        items=[JobResponse.model_validate(j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/saved", response_model=JobSearchResponse)
async def list_saved_jobs(
    viewed: bool | None = None,
    applied: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """List saved jobs for the current user."""
    items, total = await service.get_saved_jobs(
        current_user.id,
        viewed=viewed,
        applied=applied,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    return JobSearchResponse(
        items=[JobResponse.model_validate(j) for j in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats")
async def get_job_stats(
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Get job statistics for the current user."""
    return await service.get_stats(user_id=current_user.id)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Get a single job posting."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id and job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    return JobResponse.model_validate(job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: uuid.UUID,
    update: JobUpdate,
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Update a job posting (mark viewed/applied, etc.)."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id and job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    updated = await service.update_job(job_id, **update.model_dump(exclude_unset=True))
    return JobResponse.model_validate(updated)


@router.post("/{job_id}/view", response_model=JobResponse)
async def mark_job_viewed(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Mark a job as viewed."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id and job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    updated = await service.mark_viewed(job_id)
    return JobResponse.model_validate(updated)


@router.post("/{job_id}/apply", response_model=JobResponse)
async def mark_job_applied(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Mark a job as applied."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id and job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    updated = await service.mark_applied(job_id)
    return JobResponse.model_validate(updated)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: JobSearchService = Depends(get_job_search_service),
):
    """Delete a job posting."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id and job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    await service.delete_job(job_id)


@router.post("/scheduler/register")
async def register_scheduled_search(
    query: str = Query(..., max_length=500),
    location: str | None = None,
    remote_only: bool = False,
    interval: ScheduleInterval = ScheduleInterval.DAILY,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a recurring scheduled job search."""
    scheduler = get_job_scheduler()
    job_id = f"scheduled_search:{current_user.id}:{hash(query + str(location))}"

    async def _scheduled_search():
        async with db as session:
            svc = JobSearchService(session=session)
            search_req = JobSearchRequest(
                query=query, location=location, remote_only=remote_only,
            )
            return await svc.search_and_store(search_req, user_id=current_user.id)

    scheduler.register(
        job_id=job_id,
        name=f"Search: {query} ({location or 'any'})",
        handler=_scheduled_search,
        interval=interval,
    )
    return {"job_id": job_id, "interval": interval.value, "status": "registered"}


@router.get("/scheduler/jobs")
async def list_scheduled_jobs(
    current_user: User = Depends(get_current_user),
):
    """List all scheduled job searches."""
    scheduler = get_job_scheduler()
    jobs = scheduler.list_jobs()
    return [
        {
            "id": j.id,
            "name": j.name,
            "interval": j.interval.value,
            "last_run": j.last_run.isoformat() if j.last_run else None,
            "next_run": j.next_run.isoformat(),
            "is_active": j.is_active,
            "run_count": j.run_count,
        }
        for j in jobs
        if current_user.is_superuser or j.id.startswith(f"scheduled_search:{current_user.id}")
    ]
