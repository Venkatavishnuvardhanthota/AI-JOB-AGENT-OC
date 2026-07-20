import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.cover_letter import (
    CoverLetterExportRequest,
    CoverLetterGenerateRequest,
    CoverLetterListItem,
    CoverLetterResponse,
)
from app.schemas.resume_optimizer import (
    AtsOptimizeRequest,
    AtsOptimizeResponse,
    AtsScoreResponse,
    KeywordAnalysisRequest,
    KeywordAnalysisResponse,
    KeywordMatch,
    KeywordSuggestion,
    OptimizeResumeRequest,
)
from app.services.ats_resume_generator import ATSResumeGenerator
from app.services.cover_letter_generator import CoverLetterGenerator
from app.services.resume_optimizer import ResumeOptimizer

router = APIRouter()


def get_resume_optimizer(db: AsyncSession = Depends(get_db)) -> ResumeOptimizer:
    return ResumeOptimizer(db)


def get_ats_resume_generator(db: AsyncSession = Depends(get_db)) -> ATSResumeGenerator:
    return ATSResumeGenerator(db)


def get_cover_letter_generator(db: AsyncSession = Depends(get_db)) -> CoverLetterGenerator:
    return CoverLetterGenerator(db)


# ── ATS Resume Optimization ──


@router.post("/optimize/score", response_model=AtsScoreResponse)
async def score_resume_ats(
    request: OptimizeResumeRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeOptimizer = Depends(get_resume_optimizer),
) -> AtsScoreResponse:
    score = await service.score_resume(
        resume_version_id=request.resume_version_id,
        job_description=request.job_description,
        company_name=request.company_name,
        job_title=request.job_title,
    )
    return score


def _to_keyword_suggestion(kw: KeywordMatch) -> KeywordSuggestion:
    return KeywordSuggestion(
        keyword=kw.keyword,
        category=kw.category,
        priority=kw.importance,
    )


@router.post("/optimize/keywords", response_model=KeywordAnalysisResponse)
async def analyze_keywords(
    request: KeywordAnalysisRequest,
    current_user: User = Depends(get_current_user),
    service: ResumeOptimizer = Depends(get_resume_optimizer),
) -> KeywordAnalysisResponse:
    result = await service.analyze_keywords(
        resume_version_id=request.resume_version_id,
        job_description=request.job_description,
    )
    return KeywordAnalysisResponse(
        job_keywords=[_to_keyword_suggestion(kw) for kw in result.get("job_keywords", [])],
        present_in_resume=result.get("present_in_resume", []),
        missing_from_resume=[_to_keyword_suggestion(kw) for kw in result.get("missing_from_resume", [])],
        coverage_percentage=result.get("coverage_percentage", 0.0),
        suggestions=result.get("suggestions", []),
    )


@router.post("/optimize/ats-generate", response_model=AtsOptimizeResponse)
async def generate_ats_optimized_resume(
    request: AtsOptimizeRequest,
    current_user: User = Depends(get_current_user),
    service: ATSResumeGenerator = Depends(get_ats_resume_generator),
) -> AtsOptimizeResponse:
    result = await service.generate_ats_optimized(
        resume_version_id=request.resume_version_id,
        job_description=request.job_description,
        company_name=request.company_name,
        job_title=request.job_title,
    )
    return result


# ── Cover Letters ──


@router.post("/cover-letters/generate", response_model=CoverLetterResponse, status_code=201)
async def generate_cover_letter(
    request: CoverLetterGenerateRequest,
    current_user: User = Depends(get_current_user),
    service: CoverLetterGenerator = Depends(get_cover_letter_generator),
) -> CoverLetterResponse:
    cl = await service.generate(
        user_id=current_user.id,
        job_title=request.job_title,
        company_name=request.company_name,
        job_description=request.job_description,
        hiring_manager_name=request.hiring_manager_name,
        user_full_name=request.user_full_name,
        current_role=request.current_role,
        years_experience=request.years_experience,
        field=request.field,
        key_skills=request.key_skills,
        relevant_experience=request.relevant_experience,
        reason_for_interest=request.reason_for_interest,
        resume_snapshot=request.resume_snapshot,
        tone=request.tone or "professional",
        length=request.length or "medium",
        include_company_research=request.include_company_research,
    )
    if request.export_format:
        cl = await service.export_cover_letter(cl.id, current_user.id, request.export_format)
    return CoverLetterResponse.model_validate(cl)


@router.get("/cover-letters", response_model=list[CoverLetterListItem])
async def list_cover_letters(
    current_user: User = Depends(get_current_user),
    service: CoverLetterGenerator = Depends(get_cover_letter_generator),
) -> list[CoverLetterListItem]:
    letters = await service.list_cover_letters(current_user.id)
    return [CoverLetterListItem.model_validate(cl) for cl in letters]


@router.get("/cover-letters/{cover_letter_id}", response_model=CoverLetterResponse)
async def get_cover_letter(
    cover_letter_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CoverLetterGenerator = Depends(get_cover_letter_generator),
) -> CoverLetterResponse:
    cl = await service.get_cover_letter(cover_letter_id, current_user.id)
    if not cl:
        raise HTTPException(status_code=404, detail="Cover letter not found.")
    return CoverLetterResponse.model_validate(cl)


@router.delete("/cover-letters/{cover_letter_id}", status_code=204)
async def delete_cover_letter(
    cover_letter_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CoverLetterGenerator = Depends(get_cover_letter_generator),
) -> None:
    deleted = await service.delete_cover_letter(cover_letter_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cover letter not found.")


@router.post("/cover-letters/{cover_letter_id}/export", response_model=CoverLetterResponse)
async def export_cover_letter(
    cover_letter_id: uuid.UUID,
    request: CoverLetterExportRequest,
    current_user: User = Depends(get_current_user),
    service: CoverLetterGenerator = Depends(get_cover_letter_generator),
) -> CoverLetterResponse:
    cl = await service.export_cover_letter(cover_letter_id, current_user.id, request.format)
    if not cl:
        raise HTTPException(status_code=404, detail="Cover letter not found.")
    return CoverLetterResponse.model_validate(cl)
