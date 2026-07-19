import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.application_run import ManualApplyRequest, RunListItem, RunResponse
from app.schemas.application_schedule import (
    ScheduleCreateRequest,
    ScheduleListItem,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from app.schemas.notification import (
    MarkReadRequest,
    NotificationListItem,
    UnreadCountResponse,
)
from app.services.application_automation import ApplicationAutomationService
from app.services.notification_service import NotificationService
from app.services.schedule_service import ApplicationRunService, ScheduleService

router = APIRouter()


def get_schedule_service(
    db: AsyncSession = Depends(get_db),
) -> ScheduleService:
    return ScheduleService(db)


def get_automation_service(
    db: AsyncSession = Depends(get_db),
) -> ApplicationAutomationService:
    return ApplicationAutomationService(db)


def get_run_service(
    db: AsyncSession = Depends(get_db),
) -> ApplicationRunService:
    return ApplicationRunService(db)


def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(db)


# ── Schedules ──


@router.post("/schedules", response_model=ScheduleResponse, status_code=201)
async def create_schedule(
    request: ScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    schedule = await service.create(
        user_id=current_user.id,
        name=request.name,
        schedule_type=request.schedule_type,
        cron_expression=request.cron_expression,
        timezone_str=request.timezone,
        max_applications_per_day=request.max_applications_per_day,
        days_of_week=request.days_of_week,
        time_of_day=request.time_of_day,
    )
    return ScheduleResponse.model_validate(schedule)


@router.get("/schedules", response_model=list[ScheduleListItem])
async def list_schedules(
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> list[ScheduleListItem]:
    schedules = await service.list_by_user(current_user.id)
    return [ScheduleListItem.model_validate(s) for s in schedules]


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    schedule = await service.get(schedule_id, current_user.id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    return ScheduleResponse.model_validate(schedule)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    request: ScheduleUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    kwargs = request.model_dump(exclude_unset=True)
    schedule = await service.update(schedule_id, current_user.id, **kwargs)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    return ScheduleResponse.model_validate(schedule)


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> None:
    deleted = await service.delete(schedule_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found.")


# ── Schedule Control ──


@router.post("/schedules/{schedule_id}/start", response_model=ScheduleResponse)
async def start_schedule(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    schedule = await service.start(schedule_id, current_user.id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    return ScheduleResponse.model_validate(schedule)


@router.post("/schedules/{schedule_id}/stop", response_model=ScheduleResponse)
async def stop_schedule(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    schedule = await service.stop(schedule_id, current_user.id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    return ScheduleResponse.model_validate(schedule)


@router.post("/schedules/{schedule_id}/pause", response_model=ScheduleResponse)
async def pause_schedule(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    schedule = await service.pause(schedule_id, current_user.id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    return ScheduleResponse.model_validate(schedule)


@router.post("/schedules/{schedule_id}/resume", response_model=ScheduleResponse)
async def resume_schedule(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleResponse:
    schedule = await service.resume(schedule_id, current_user.id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    return ScheduleResponse.model_validate(schedule)


# ── Manual Apply / Runs ──


@router.post("/runs", response_model=RunResponse, status_code=201)
async def manual_apply(
    request: ManualApplyRequest,
    current_user: User = Depends(get_current_user),
    service: ApplicationAutomationService = Depends(get_automation_service),
) -> RunResponse:
    run = await service.manual_apply(
        user_id=current_user.id,
        job_ids=request.job_ids,
        max_applications=request.max_applications,
        schedule_id=request.schedule_id,
    )
    return RunResponse.model_validate(run)


@router.get("/runs", response_model=list[RunListItem])
async def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: ApplicationRunService = Depends(get_run_service),
) -> list[RunListItem]:
    runs = await service.list_by_user(current_user.id, skip=skip, limit=limit)
    return [RunListItem.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationRunService = Depends(get_run_service),
) -> RunResponse:
    run = await service.get(run_id, current_user.id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    return RunResponse.model_validate(run)


# ── Notifications ──


@router.get("/notifications", response_model=list[NotificationListItem])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationListItem]:
    notifications = await service.list_by_user(
        current_user.id, skip=skip, limit=limit, unread_only=unread_only,
    )
    return [NotificationListItem.model_validate(n) for n in notifications]


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
async def unread_notification_count(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> UnreadCountResponse:
    count = await service.unread_count(current_user.id)
    return UnreadCountResponse(count=count)


@router.post("/notifications/mark-read", response_model=dict)
async def mark_notifications_read(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> dict:
    updated = await service.mark_read(current_user.id, request.notification_ids)
    return {"marked_read": updated}


# ── Stats ──


@router.get("/stats")
async def get_apply_stats(
    current_user: User = Depends(get_current_user),
    service: ApplicationAutomationService = Depends(get_automation_service),
) -> dict:
    return await service.get_daily_stats(current_user.id)
