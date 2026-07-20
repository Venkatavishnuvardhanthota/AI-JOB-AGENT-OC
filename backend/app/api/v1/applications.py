import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.application import ApplicationRepository
from app.schemas.application import ApplicationPrepareRequest, ApplicationResponse
from app.services.application import ApplicationService

router = APIRouter()


@router.get("/")
async def list_applications(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ApplicationService(db)
    result = await service.list_applications(current_user.id, status=status, page=page, page_size=page_size)
    return {"success": True, **result}


@router.post("/prepare", status_code=201)
async def prepare_application(
    body: ApplicationPrepareRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ApplicationService(db)
    app = await service.prepare(
        user_id=current_user.id,
        job_id=body.job_id,
        resume_id=body.resume_id,
        generate_cover_letter=body.generate_cover_letter,
        generate_ai_answers=body.generate_ai_answers,
    )
    return {"success": True, "data": {"application_id": str(app.id), "status": app.status}}


@router.get("/{application_id}")
async def get_application(
    application_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ApplicationService(db)
    app = await service.get_application(uuid.UUID(application_id))
    return {"success": True, "data": ApplicationResponse.model_validate(app).model_dump()}


@router.post("/{application_id}/submit")
async def submit_application(
    application_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ApplicationService(db)
    app = await service.submit(uuid.UUID(application_id))
    return {
        "success": True,
        "data": {
            "status": app.status,
            "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        },
    }


@router.post("/{application_id}/cancel")
async def cancel_application(
    application_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ApplicationService(db)
    app = await service.cancel(uuid.UUID(application_id))
    return {"success": True, "data": {"status": app.status}}


@router.get("/{application_id}/timeline")
async def application_timeline(
    application_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    app_repo = ApplicationRepository(db)
    app = await app_repo.get_by_id(uuid.UUID(application_id))
    entries = []
    if app:
        entries.append({"event": "Application Prepared", "timestamp": app.created_at.isoformat()})
        if app.submitted_at:
            entries.append({"event": "Submitted", "timestamp": app.submitted_at.isoformat()})
    return {"success": True, "data": entries}


@router.get("/{application_id}/status")
async def application_status(
    application_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    app_repo = ApplicationRepository(db)
    app = await app_repo.get_by_id(uuid.UUID(application_id))
    if not app:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Application not found.")
    return {"success": True, "data": {"status": app.status, "last_updated": app.updated_at.isoformat()}}
