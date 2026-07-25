import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.resume import (
    ResumeCreate,
    ResumeExportData,
    ResumeImportData,
    ResumeListResponse,
    ResumeResponse,
    ResumeSectionCreate,
    ResumeSectionResponse,
    ResumeSectionUpdate,
    ResumeUpdate,
    ResumeVersionCreate,
)
from app.services.resume import ResumeService

router = APIRouter()


@router.get("/")
@router.get("")
async def list_resumes(
    current_user: User = Depends(get_current_user),
    archived: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resumes = await service.list_resumes(current_user.id, archived=archived)
    items = []
    for r in resumes:
        try:
            section_count = len(r.sections) if r.sections else 0
        except Exception:
            section_count = 0
        items.append(
            ResumeListResponse(
                id=r.id,
                version=r.version,
                title=r.title,
                template=r.template,
                status=r.status,
                source=r.source,
                is_default=r.is_default,
                archived=r.archived,
                section_count=section_count,
                created_at=r.created_at,
            ).model_dump()
        )
    return {"success": True, "data": items}


@router.post("/", status_code=201)
@router.post("", status_code=201)
async def create_resume(
    body: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.create_resume(
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        template=body.template,
        resume_type=body.resume_type,
        change_summary=body.change_summary,
        sections=[s.model_dump() for s in body.sections] if body.sections else None,
    )
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.get_resume(uuid.UUID(resume_id), current_user.id)
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.patch("/{resume_id}")
async def update_resume(
    resume_id: str,
    body: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.update_resume(
        uuid.UUID(resume_id),
        current_user.id,
        body.model_dump(exclude_none=True),
    )
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    await service.delete_resume(uuid.UUID(resume_id), current_user.id)


@router.post("/{resume_id}/archive")
async def archive_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.archive_resume(uuid.UUID(resume_id), current_user.id)
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.post("/{resume_id}/restore")
async def restore_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.restore_resume(uuid.UUID(resume_id), current_user.id)
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.post("/{resume_id}/versions", status_code=201)
async def create_resume_version(
    resume_id: str,
    body: ResumeVersionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.create_version(
        uuid.UUID(resume_id),
        current_user.id,
        change_summary=body.change_summary,
    )
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.put("/{resume_id}/default")
async def set_default_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.set_default_resume(uuid.UUID(resume_id), current_user.id)
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.post("/import", status_code=201)
async def import_resume(
    body: ResumeImportData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.import_resume(current_user.id, body)
    await service.audit_service.log(
        "RESUME_IMPORTED",
        user_id=current_user.id,
        entity="resume",
        entity_id=resume.id,
        outcome="success",
    )
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.get("/{resume_id}/export")
async def export_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.export_resume(uuid.UUID(resume_id), current_user.id)
    export_data = ResumeExportData(
        version=resume.version,
        title=resume.title,
        description=resume.description,
        template=resume.template,
        resume_type=resume.resume_type,
        status=resume.status,
        source=resume.source,
        change_summary=resume.change_summary,
        sections=[ResumeSectionResponse.model_validate(s) for s in (resume.sections or [])],
        created_at=resume.created_at,
        updated_at=resume.updated_at,
    )
    await service.audit_service.log(
        "RESUME_EXPORTED",
        user_id=current_user.id,
        entity="resume",
        entity_id=resume.id,
        outcome="success",
    )
    return {"success": True, "data": export_data.model_dump()}


# ── Sections ──


@router.get("/{resume_id}/sections")
async def list_sections(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resume = await service.get_resume(uuid.UUID(resume_id), current_user.id)
    sections = resume.sections or []
    return {
        "success": True,
        "data": [ResumeSectionResponse.model_validate(s).model_dump() for s in sections],
    }


@router.post("/{resume_id}/sections", status_code=201)
async def add_section(
    resume_id: str,
    body: ResumeSectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    section = await service.add_section(uuid.UUID(resume_id), current_user.id, body.model_dump())
    return {"success": True, "data": ResumeSectionResponse.model_validate(section).model_dump()}


@router.patch("/{resume_id}/sections/{section_id}")
async def update_section(
    resume_id: str,
    section_id: str,
    body: ResumeSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    section = await service.update_section(
        uuid.UUID(section_id),
        current_user.id,
        body.model_dump(exclude_none=True),
    )
    return {"success": True, "data": ResumeSectionResponse.model_validate(section).model_dump()}


@router.delete("/{resume_id}/sections/{section_id}", status_code=204)
async def delete_section(
    resume_id: str,
    section_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    await service.delete_section(uuid.UUID(section_id), current_user.id)


# ── Templates ──


@router.get("/templates")
async def list_templates(
    db: AsyncSession = Depends(get_db),
):
    from app.repositories import ResumeTemplateRepository

    repo = ResumeTemplateRepository(db)
    templates = await repo.list_by_user(uuid.UUID(int=0))
    return {
        "success": True,
        "data": [{"id": str(t.id), "name": t.name} for t in templates],
    }
