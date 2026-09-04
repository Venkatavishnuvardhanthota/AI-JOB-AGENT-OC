import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import ValidationError as AppValidationError
from app.models import User
from app.schemas.cover_letter import (
    ApplicationPackageRequest,
    CoverLetterAIAssistRequest,
    CoverLetterCreate,
    CoverLetterGenerateRequest,
    CoverLetterListItem,
    CoverLetterResponse,
    CoverLetterUpdate,
)
from app.services.cover_letter import CoverLetterService

router = APIRouter()


@router.get("/")
@router.get("")
async def list_cover_letters(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    items = await service.list_by_user(current_user.id, status=status)
    return {
        "success": True,
        "data": [CoverLetterListItem.model_validate(cl).model_dump() for cl in items],
    }


@router.post("/", status_code=201)
@router.post("", status_code=201)
async def create_cover_letter(
    body: CoverLetterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    cl = await service.create(current_user.id, body.model_dump(exclude_none=True))
    return {"success": True, "data": CoverLetterResponse.model_validate(cl).model_dump()}


@router.get("/{cover_letter_id}")
async def get_cover_letter(
    cover_letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    cl = await service.get(uuid.UUID(cover_letter_id), current_user.id)
    return {"success": True, "data": CoverLetterResponse.model_validate(cl).model_dump()}


@router.patch("/{cover_letter_id}")
async def update_cover_letter(
    cover_letter_id: str,
    body: CoverLetterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    cl = await service.update(uuid.UUID(cover_letter_id), current_user.id, body.model_dump(exclude_none=True))
    return {"success": True, "data": CoverLetterResponse.model_validate(cl).model_dump()}


@router.delete("/{cover_letter_id}", status_code=204)
async def delete_cover_letter(
    cover_letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    await service.delete(uuid.UUID(cover_letter_id), current_user.id)


@router.post("/{cover_letter_id}/duplicate", status_code=201)
async def duplicate_cover_letter(
    cover_letter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    cl = await service.duplicate(uuid.UUID(cover_letter_id), current_user.id)
    return {"success": True, "data": CoverLetterResponse.model_validate(cl).model_dump()}


@router.post("/generate", status_code=201)
async def generate_cover_letter(
    body: CoverLetterGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    cl = await service.generate_ai(
        user_id=current_user.id,
        job_id=uuid.UUID(body.job_id),
        resume_id=uuid.UUID(body.resume_id),
        tone=body.tone,
        template=body.template or "modern",
        hiring_manager=body.hiring_manager,
        additional_notes=body.additional_notes,
    )
    return {"success": True, "data": CoverLetterResponse.model_validate(cl).model_dump()}


@router.post("/{cover_letter_id}/ai-assist")
async def ai_assist_cover_letter(
    cover_letter_id: str,
    body: CoverLetterAIAssistRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    cl = await service.get(uuid.UUID(cover_letter_id), current_user.id)
    edited = await service.ai_assist(body.section or (cl.content or ""), body.instruction, body.context)
    return {"success": True, "data": {"original": cl.content, "edited": edited}}


@router.get("/{cover_letter_id}/export/{format}")
async def export_cover_letter(
    cover_letter_id: str,
    format: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    cid = uuid.UUID(cover_letter_id)
    if format == "pdf":
        content = await service.export_pdf(cid, current_user.id)
        return Response(content=content, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="cover-letter.pdf"'})
    elif format == "docx":
        content = await service.export_docx(cid, current_user.id)
        return Response(content=content,
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        headers={"Content-Disposition": f'attachment; filename="cover-letter.docx"'})
    elif format == "txt":
        cl = await service.get(cid, current_user.id)
        return Response(content=cl.content or "", media_type="text/plain",
                        headers={"Content-Disposition": f'attachment; filename="cover-letter.txt"'})
    raise AppValidationError(f"Unsupported format: {format}. Use 'pdf', 'docx', or 'txt'.")


@router.post("/application-package")
async def create_application_package(
    body: ApplicationPackageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CoverLetterService(db)
    result = await service.create_application_package(
        user_id=current_user.id,
        resume_id=uuid.UUID(body.resume_id),
        cover_letter_id=uuid.UUID(body.cover_letter_id),
        job_id=uuid.UUID(body.job_id),
        notes=body.notes,
    )
    return {"success": True, "data": result}
