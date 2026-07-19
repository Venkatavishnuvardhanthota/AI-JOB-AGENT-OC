import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.interview_prep import (
    InterviewPrepGenerateRequest,
    InterviewPrepListItem,
    InterviewPrepResponse,
    TruthValidateRequest,
    TruthValidateResponse,
    TruthValidationResult,
)
from app.services.interview_prep import InterviewPrepService
from app.services.truth_validator import TruthValidator

router = APIRouter()


def get_interview_prep_service(
    db: AsyncSession = Depends(get_db),
) -> InterviewPrepService:
    return InterviewPrepService(db)


@router.post("/interview-prep/generate", response_model=InterviewPrepResponse, status_code=201)
async def generate_interview_prep(
    request: InterviewPrepGenerateRequest,
    current_user: User = Depends(get_current_user),
    service: InterviewPrepService = Depends(get_interview_prep_service),
) -> InterviewPrepResponse:
    prep = await service.generate(
        user_id=current_user.id,
        job_title=request.job_title,
        company_name=request.company_name,
        job_description=request.job_description,
        resume_snapshot=request.resume_snapshot,
        company_research=request.company_research,
        include_behavioral=request.include_behavioral,
        include_technical=request.include_technical,
        include_salary=request.include_salary,
        include_notice_period=request.include_notice_period,
        include_strengths_weaknesses=request.include_strengths_weaknesses,
        include_career_goals=request.include_career_goals,
        include_company_specific=request.include_company_specific,
    )
    return InterviewPrepResponse.model_validate(prep)


@router.get("/interview-prep", response_model=list[InterviewPrepListItem])
async def list_interview_preps(
    current_user: User = Depends(get_current_user),
    service: InterviewPrepService = Depends(get_interview_prep_service),
) -> list[InterviewPrepListItem]:
    preps = await service.list_by_user(current_user.id)
    return [InterviewPrepListItem.model_validate(p) for p in preps]


@router.get("/interview-prep/{prep_id}", response_model=InterviewPrepResponse)
async def get_interview_prep(
    prep_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: InterviewPrepService = Depends(get_interview_prep_service),
) -> InterviewPrepResponse:
    prep = await service.get(prep_id, current_user.id)
    if not prep:
        raise HTTPException(status_code=404, detail="Interview prep not found.")
    return InterviewPrepResponse.model_validate(prep)


@router.delete("/interview-prep/{prep_id}", status_code=204)
async def delete_interview_prep(
    prep_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: InterviewPrepService = Depends(get_interview_prep_service),
) -> None:
    deleted = await service.delete(prep_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Interview prep not found.")


@router.post("/interview-prep/validate-truth", response_model=TruthValidateResponse)
async def validate_truth(
    request: TruthValidateRequest,
    current_user: User = Depends(get_current_user),
    validator: TruthValidator = Depends(lambda: TruthValidator()),
) -> TruthValidateResponse:
    results = await validator.validate(request.statements, request.context)
    return TruthValidateResponse(
        results=[TruthValidationResult(**r) for r in results]
    )
