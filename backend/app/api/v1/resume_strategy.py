from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.resume_strategy import (
    RESUME_STRATEGY_ASK,
    ResumeStrategyPrepareRequest,
    ResumeStrategyPreviewRequest,
    ResumeStrategyPreviewResponse,
    ResumeStrategySettings,
    ResumeStrategySettingsUpdate,
)
from app.services.resume_strategy import ResumeStrategyService

router = APIRouter()


@router.get("/settings/resume-strategy")
async def get_resume_strategy(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = ResumeStrategyService(db)
    settings = await service.get_settings(current_user.id)
    return {
        "success": True,
        "data": ResumeStrategySettings(
            resume_strategy=settings.resume_strategy,
            save_generated_resumes=settings.save_generated_resumes,
        ).model_dump(),
    }


@router.put("/settings/resume-strategy")
async def update_resume_strategy(
    body: ResumeStrategySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeStrategyService(db)
    settings = await service.update_settings(
        current_user.id,
        resume_strategy=body.resume_strategy.value if body.resume_strategy else None,
        save_generated_resumes=body.save_generated_resumes.value if body.save_generated_resumes else None,
    )
    return {
        "success": True,
        "data": ResumeStrategySettings(
            resume_strategy=settings.resume_strategy,
            save_generated_resumes=settings.save_generated_resumes,
        ).model_dump(),
    }


@router.post("/strategy/preview")
async def strategy_preview(
    body: ResumeStrategyPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ResumeStrategyService(db)
    preview = await service.preview(current_user.id, body.job_id)
    return {"success": True, "data": ResumeStrategyPreviewResponse(**preview).model_dump()}


@router.post("/strategy/select", status_code=201)
async def strategy_select(
    body: ResumeStrategyPrepareRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complete an application preparation with an explicit strategy (used after an `ask` decision)."""
    service = ResumeStrategyService(db)
    result = await service.prepare_application(
        user_id=current_user.id,
        job_id=body.job_id,
        strategy_override=body.strategy_override.value if body.strategy_override else None,
        resume_id=body.resume_id,
        generate_cover_letter=body.generate_cover_letter,
    )
    if result.get("needs_choice") or result.get("strategy") == RESUME_STRATEGY_ASK:
        return {
            "success": True,
            "data": {
                "needs_choice": True,
                "message": (
                    "No strategy provided. Call /applications/prepare with "
                    "resume_strategy_override or retry with an explicit strategy."
                ),
            },
        }
    return {"success": True, "data": result}
