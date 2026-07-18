import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resume import (
    CreateVersionFromSnapshot,
    GeneratedResumeResponse,
    GenerateResumeRequest,
    ResumeMasterCreate,
    ResumeMasterResponse,
    ResumeMasterUpdate,
    ResumeTemplateCreate,
    ResumeTemplateResponse,
    ResumeVersionCreate,
    ResumeVersionResponse,
)
from app.services.resume import ResumeService

router = APIRouter()


def get_resume_service(db: AsyncSession = Depends(get_db)) -> ResumeService:
    return ResumeService(db)


# ── Resume Masters ──

@router.get("/masters", response_model=list[ResumeMasterResponse])
async def list_masters(
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> list[ResumeMasterResponse]:
    masters = await service.list_masters(current_user.id)
    return [ResumeMasterResponse.model_validate(m) for m in masters]


@router.post("/masters", response_model=ResumeMasterResponse, status_code=201)
async def create_master(
    request: ResumeMasterCreate,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeMasterResponse:
    master = await service.create_master(
        user_id=current_user.id,
        name=request.name,
        title=request.title,
        summary=request.summary,
        template_id=request.template_id,
    )
    return ResumeMasterResponse.model_validate(master)


@router.get("/masters/{master_id}", response_model=ResumeMasterResponse)
async def get_master(
    master_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeMasterResponse:
    master = await service.get_master(master_id, current_user.id)
    if not master:
        raise HTTPException(status_code=404, detail="Resume master not found.")
    return ResumeMasterResponse.model_validate(master)


@router.put("/masters/{master_id}", response_model=ResumeMasterResponse)
async def update_master(
    master_id: uuid.UUID,
    request: ResumeMasterUpdate,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeMasterResponse:
    master = await service.update_master(
        master_id, current_user.id,
        **request.model_dump(exclude_unset=True),
    )
    if not master:
        raise HTTPException(status_code=404, detail="Resume master not found.")
    return ResumeMasterResponse.model_validate(master)


@router.delete("/masters/{master_id}", status_code=204)
async def delete_master(
    master_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> None:
    deleted = await service.delete_master(master_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume master not found.")


# ── Resume Versions ──

@router.get("/masters/{master_id}/versions", response_model=list[ResumeVersionResponse])
async def list_versions(
    master_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> list[ResumeVersionResponse]:
    versions = await service.list_versions(master_id, current_user.id)
    return [ResumeVersionResponse.model_validate(v) for v in versions]


@router.post("/masters/{master_id}/versions", response_model=ResumeVersionResponse, status_code=201)
async def create_version(
    master_id: uuid.UUID,
    request: ResumeVersionCreate,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeVersionResponse:
    version = await service.create_version(
        master_id=master_id,
        user_id=current_user.id,
        name=request.name,
        notes=request.notes,
        snapshot_data=request.snapshot_data,
    )
    if not version:
        raise HTTPException(status_code=404, detail="Resume master not found.")
    return ResumeVersionResponse.model_validate(version)


@router.post("/masters/{master_id}/versions/from-snapshot", response_model=ResumeVersionResponse, status_code=201)
async def create_version_from_snapshot(
    master_id: uuid.UUID,
    request: CreateVersionFromSnapshot,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeVersionResponse:
    snapshot = await service.build_snapshot_from_selections(
        user_id=current_user.id,
        profile_fields=request.profile_fields,
        education_ids=request.education_ids,
        experience_ids=request.experience_ids,
        skill_ids=request.skill_ids,
        project_ids=request.project_ids,
        certification_ids=request.certification_ids,
        language_ids=request.language_ids,
        portfolio_item_ids=request.portfolio_item_ids,
    )
    version = await service.create_version(
        master_id=master_id,
        user_id=current_user.id,
        name=request.name,
        notes=request.notes,
        snapshot_data=snapshot,
    )
    if not version:
        raise HTTPException(status_code=404, detail="Resume master not found.")
    return ResumeVersionResponse.model_validate(version)


@router.get("/versions/{version_id}", response_model=ResumeVersionResponse)
async def get_version(
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeVersionResponse:
    version = await service.get_version(version_id, current_user.id)
    if not version:
        raise HTTPException(status_code=404, detail="Resume version not found.")
    return ResumeVersionResponse.model_validate(version)


@router.get("/versions/{version_id}/snapshot", response_model=dict)
async def get_version_snapshot(
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> dict:
    snapshot = await service.get_version_snapshot(version_id, current_user.id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Resume version not found.")
    return snapshot


# ── Resume Generation ──

@router.post("/generate", response_model=GeneratedResumeResponse, status_code=201)
async def generate_resume(
    request: GenerateResumeRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> GeneratedResumeResponse:
    generated = await service.generate_resume(
        version_id=request.resume_version_id,
        user_id=current_user.id,
        output_format=request.format,
    )
    if not generated:
        raise HTTPException(
            status_code=400,
            detail="Could not generate resume. Version may be missing snapshot data.",
        )
    return GeneratedResumeResponse.model_validate(generated)


@router.get("/generated", response_model=list[GeneratedResumeResponse])
async def list_generated(
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> list[GeneratedResumeResponse]:
    items = await service.list_generated(current_user.id)
    return [GeneratedResumeResponse.model_validate(g) for g in items]


# ── Templates ──

@router.get("/templates", response_model=list[ResumeTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> list[ResumeTemplateResponse]:
    templates = await service.list_templates(current_user.id)
    return templates


@router.get("/templates/builtin", response_model=list[dict])
async def list_builtin_templates(
    service: ResumeService = Depends(get_resume_service),
) -> list[dict]:
    return service.generator.get_available_templates()


@router.post("/templates", response_model=ResumeTemplateResponse, status_code=201)
async def create_template(
    request: ResumeTemplateCreate,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeTemplateResponse:
    tmpl = await service.create_template(
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        layout_config=request.layout_config,
    )
    return ResumeTemplateResponse.model_validate(tmpl)


# ── Parse uploaded resume ──

@router.post("/parse", response_model=dict)
async def parse_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> dict:
    from app.services.resume_parser import ResumeParserService
    from app.services.storage import FileStorageService

    storage = FileStorageService()
    file_path = await storage.save(file, f"users/{current_user.id}/parsed")
    parser = ResumeParserService()
    try:
        result = parser.parse_file(file_path)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Uploaded file not found.") from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}") from e
