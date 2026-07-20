import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import MissingGreenlet
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.application_tracking import (
    ApplicationAnalytics,
    ApplicationCreateRequest,
    ApplicationListItem,
    ApplicationResponse,
    ApplicationUpdateRequest,
    NoteCreateRequest,
    NoteResponse,
    TagCreateRequest,
    TagResponse,
    TagUpdateRequest,
    TimelineEventResponse,
)
from app.services.application_tracking import (
    ApplicationAnalyticsService,
    ApplicationExportService,
    ApplicationTrackingService,
)

router = APIRouter()


def get_tracking_service(
    db: AsyncSession = Depends(get_db),
) -> ApplicationTrackingService:
    return ApplicationTrackingService(db)


def get_analytics_service(
    db: AsyncSession = Depends(get_db),
) -> ApplicationAnalyticsService:
    return ApplicationAnalyticsService(db)


def get_export_service(
    db: AsyncSession = Depends(get_db),
) -> ApplicationExportService:
    return ApplicationExportService(db)


# ── Applications CRUD ──


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    request: ApplicationCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> ApplicationResponse:
    try:
        app = await service.create(
            user_id=current_user.id,
            job_posting_id=request.job_posting_id,
            job_title=request.job_title,
            company_name=request.company_name,
            job_url=request.job_url,
            location=request.location,
            salary_range=request.salary_range,
            status=request.status,
            notes=request.notes,
            tag_ids=request.tag_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _app_to_response(app)


@router.get("", response_model=dict)
async def list_applications(
    status: str | None = Query(None),
    company_name: str | None = Query(None),
    search: str | None = Query(None),
    tag_ids: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    is_active: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> dict:
    parsed_tag_ids = []
    if tag_ids:
        try:
            parsed_tag_ids = [uuid.UUID(t) for t in tag_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tag_ids format.") from None
    apps, total = await service.list_by_user(
        user_id=current_user.id,
        status=status,
        company_name=company_name,
        search=search,
        tag_ids=parsed_tag_ids,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [_app_to_list_item(a) for a in apps],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ── Duplicate Check ──


@router.get("/check-duplicate/{job_posting_id}")
async def check_duplicate(
    job_posting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> dict:
    existing = await service.check_duplicate(current_user.id, job_posting_id)
    return {"is_duplicate": existing is not None, "application_id": str(existing.id) if existing else None}


# ── Tags CRUD (must be before /{app_id} routes) ──


@router.post("/tags", response_model=TagResponse, status_code=201)
async def create_tag(
    request: TagCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> TagResponse:
    tag = await service.create_tag(current_user.id, request.name, request.color)
    return TagResponse.model_validate(tag)


@router.get("/tags", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> list[TagResponse]:
    tags = await service.list_tags(current_user.id)
    return [TagResponse.model_validate(t) for t in tags]


@router.patch("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    request: TagUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> TagResponse:
    kwargs = request.model_dump(exclude_unset=True)
    tag = await service.update_tag(tag_id, current_user.id, **kwargs)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found.")
    return TagResponse.model_validate(tag)


@router.delete("/tags/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> None:
    deleted = await service.delete_tag(tag_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found.")


# ── Analytics ──


@router.get("/analytics/overview", response_model=ApplicationAnalytics)
async def get_analytics(
    current_user: User = Depends(get_current_user),
    service: ApplicationAnalyticsService = Depends(get_analytics_service),
) -> ApplicationAnalytics:
    data = await service.get_analytics(current_user.id)
    return ApplicationAnalytics(**data)


# ── Export (must be before /{app_id} routes) ──


@router.get("/export/csv")
async def export_csv(
    current_user: User = Depends(get_current_user),
    service: ApplicationExportService = Depends(get_export_service),
):
    from fastapi.responses import PlainTextResponse

    csv_content = await service.export_csv(current_user.id)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"},
    )


# ── Application Detail CRUD (/{app_id} routes — must be AFTER static routes) ──


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> ApplicationResponse:
    app = await service.get(app_id, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    return _app_to_response(app)


@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: uuid.UUID,
    request: ApplicationUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> ApplicationResponse:
    kwargs = request.model_dump(exclude_unset=True)
    app = await service.update(app_id, current_user.id, **kwargs)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    return _app_to_response(app)


@router.delete("/{app_id}", status_code=204)
async def delete_application(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> None:
    deleted = await service.delete(app_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Application not found.")


# ── Notes ──


@router.post("/{app_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(
    app_id: uuid.UUID,
    request: NoteCreateRequest,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> NoteResponse:
    note = await service.add_note(app_id, current_user.id, request.content)
    if not note:
        raise HTTPException(status_code=404, detail="Application not found.")
    return NoteResponse.model_validate(note)


@router.get("/{app_id}/notes", response_model=list[NoteResponse])
async def list_notes(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> list[NoteResponse]:
    notes = await service.get_notes(app_id, current_user.id)
    return [NoteResponse.model_validate(n) for n in notes]


# ── Tags on Applications ──


@router.post("/{app_id}/tags/{tag_id}", response_model=dict)
async def add_tag_to_application(
    app_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> dict:
    ok = await service.add_tag_to_application(app_id, current_user.id, tag_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Application not found.")
    return {"success": True}


@router.delete("/{app_id}/tags/{tag_id}")
async def remove_tag_from_application(
    app_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> dict:
    ok = await service.remove_tag_from_application(app_id, current_user.id, tag_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Application or tag mapping not found.")
    return {"success": True}


# ── Timeline ──


@router.get("/{app_id}/timeline", response_model=list[TimelineEventResponse])
async def get_timeline(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ApplicationTrackingService = Depends(get_tracking_service),
) -> list[TimelineEventResponse]:
    events = await service.get_timeline(app_id, current_user.id)
    return [TimelineEventResponse.model_validate(e) for e in events]


# ── Helpers ──


def _safe_rel(obj, attr, default=None):
    try:
        return getattr(obj, attr)
    except MissingGreenlet:
        return default


def _app_to_response(app) -> ApplicationResponse:
    tag_mappings = _safe_rel(app, "tag_mappings", []) or []
    tags = []
    for m in tag_mappings:
        if m.tag:
            tags.append(TagResponse.model_validate(m.tag))
    notes = _safe_rel(app, "notes", []) or []
    note_count = len(notes)
    timeline_events = _safe_rel(app, "timeline_events", []) or []
    last_event = None
    if timeline_events:
        sorted_events = sorted(timeline_events, key=lambda e: e.occurred_at, reverse=True)
        last_event = TimelineEventResponse.model_validate(sorted_events[0]) if sorted_events else None
    return ApplicationResponse(
        id=app.id,
        user_id=app.user_id,
        job_posting_id=app.job_posting_id,
        run_id=app.run_id,
        status=app.status,
        job_title=app.job_title,
        company_name=app.company_name,
        job_url=app.job_url,
        location=app.location,
        salary_range=app.salary_range,
        applied_at=app.applied_at,
        is_active=app.is_active,
        tags=tags,
        note_count=note_count,
        last_timeline_event=last_event,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


def _app_to_list_item(app) -> ApplicationListItem:
    tag_mappings = _safe_rel(app, "tag_mappings", []) or []
    tags = []
    for m in tag_mappings:
        if m.tag:
            tags.append(TagResponse.model_validate(m.tag))
    return ApplicationListItem(
        id=app.id,
        job_posting_id=app.job_posting_id,
        status=app.status,
        job_title=app.job_title,
        company_name=app.company_name,
        location=app.location,
        applied_at=app.applied_at,
        is_active=app.is_active,
        tags=tags,
        created_at=app.created_at,
    )
