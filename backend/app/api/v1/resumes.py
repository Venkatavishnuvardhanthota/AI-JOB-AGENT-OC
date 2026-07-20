import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resume import ResumeCreate, ResumeListResponse, ResumeResponse
from app.services.resume import ResumeService

router = APIRouter()


@router.get("/")
async def list_resumes(
    current_user: User = Depends(get_current_user),
    archived: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeService(db)
    resumes = await service.list_resumes(current_user.id, archived=archived)
    return {"success": True, "data": [ResumeListResponse.model_validate(r).model_dump() for r in resumes]}


@router.post("/generate", status_code=201)
async def generate_resume(
    body: ResumeCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    resume = await service.generate_resume(
        user_id=current_user.id,
        job_id=body.job_id,
        template=body.template,
        title=body.title,
    )
    return {
        "success": True,
        "data": {
            "resume_id": str(resume.id),
            "version": resume.version,
            "status": "generated",
        },
    }


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    resume = await service.get_resume(uuid.UUID(resume_id))
    return {"success": True, "data": ResumeResponse.model_validate(resume).model_dump()}


@router.delete("/{resume_id}", status_code=204)
async def archive_resume(
    resume_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    await service.archive_resume(uuid.UUID(resume_id))


@router.post("/{resume_id}/restore")
async def restore_resume(
    resume_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    await service.restore_resume(uuid.UUID(resume_id))
    return {"success": True, "message": "Resume restored successfully."}


@router.get("/{resume_id}/preview")
async def preview_resume(
    resume_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    resume = await service.get_resume(uuid.UUID(resume_id))
    return {"success": True, "data": {"html": f"<html><body><h1>{resume.title or 'Resume'}</h1></body></html>"}}


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ResumeService(db)
    resume = await service.get_resume(uuid.UUID(resume_id))
    return {"success": True, "data": {"content": resume.content, "format": "pdf"}}


@router.get("/templates")
async def list_templates():
    templates = [
        {"id": "modern", "name": "Modern"},
        {"id": "professional", "name": "Professional"},
        {"id": "creative", "name": "Creative"},
    ]
    return {"success": True, "data": templates}
