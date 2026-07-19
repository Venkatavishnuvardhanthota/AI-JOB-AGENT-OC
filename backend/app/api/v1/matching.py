import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.job_posting import JobPosting
from app.models.user import User
from app.schemas.matching import (
    BatchScoreRequest,
    BatchScoreResponse,
    MatchScore,
    ScoredJobResponse,
    ScoreExplanation,
    ScoringConfig,
    ScoringConfigResponse,
)
from app.services.job_search import JobSearchService
from app.services.matching.scorer import MatchScorer
from app.services.matching.threshold_filter import ThresholdFilter

router = APIRouter()

_scoring_config = ScoringConfig()


def get_scorer(db: AsyncSession = Depends(get_db)) -> MatchScorer:
    return MatchScorer(db)


@router.get("/config", response_model=ScoringConfigResponse)
async def get_scoring_config(
    current_user: User = Depends(get_current_user),
):
    """Get the current scoring configuration."""
    return ScoringConfigResponse(
        config=_scoring_config,
        updated_at=None,
    )


@router.put("/config", response_model=ScoringConfigResponse)
async def update_scoring_config(
    config: ScoringConfig,
    current_user: User = Depends(get_current_user),
):
    """Update the scoring configuration."""
    global _scoring_config  # noqa: PLW0603
    _scoring_config = config
    return ScoringConfigResponse(
        config=_scoring_config,
        updated_at=None,
    )


@router.post("/jobs/{job_id}/score", response_model=MatchScore)
async def score_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Score a job against the current user's profile."""
    stmt = select(JobPosting).where(JobPosting.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    scorer = get_scorer(db)
    score = await scorer.score_job(job, str(current_user.id), _scoring_config)
    return score


@router.post("/jobs/batch-score", response_model=BatchScoreResponse)
async def score_jobs_batch(
    req: BatchScoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Score multiple jobs against the current user's profile."""
    scorer = get_scorer(db)
    return await scorer.score_batch(req, str(current_user.id), _scoring_config)


@router.post("/jobs/{job_id}/explain", response_model=list[ScoreExplanation])
async def explain_job_score(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed score explanation for a job."""
    stmt = select(JobPosting).where(JobPosting.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    scorer = get_scorer(db)
    score = await scorer.score_job(job, str(current_user.id), _scoring_config)
    return score.explanations


@router.get("/jobs/scored", response_model=list[ScoredJobResponse])
async def list_scored_jobs(
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with match scores, filtered by minimum score and threshold."""
    service = JobSearchService(session=db)
    items, total = await service.list_jobs(
        query="",
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        is_active=True,
    )
    scorer = get_scorer(db)
    filter_ = ThresholdFilter()
    scored = []
    for job in items:
        score = await scorer.score_job(job, str(current_user.id), _scoring_config)
        if filter_.is_above_threshold(score, _scoring_config) and score.overall >= min_score:
            scored.append(ScoredJobResponse(
                id=str(job.id),
                title=job.title,
                company_name=job.company_name,
                location=job.location,
                source=job.source,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                salary_currency=job.salary_currency,
                job_type=job.job_type,
                remote=job.remote,
                posted_at=job.posted_at,
                skills=job.skills or [],
                is_active=job.is_active,
                match_score=score.overall,
                match_details=score.explanations[0] if score.explanations else None,
            ))
    return scored
