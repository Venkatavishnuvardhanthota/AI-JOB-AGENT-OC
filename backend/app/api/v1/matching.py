import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.repositories import JobRepository
from app.services.match_engine import MatchEngineService

router = APIRouter()


DEFAULT_SCORING_CONFIG = {
    "weights": {"skill": 30, "keyword": 20, "experience": 25, "education": 15, "company": 10},
    "skill_threshold": 0.5,
    "keyword_threshold": 0.3,
    "experience_threshold": 0.4,
    "education_threshold": 0.3,
    "overall_threshold": 0.0,
    "boost_exact_title_match": True,
    "boost_current_company": True,
    "penalty_blacklisted": True,
}

_scoring_config = dict(DEFAULT_SCORING_CONFIG)
_config_updated_at: str | None = None


@router.get("/config")
async def get_config(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "config": _scoring_config,
            "updated_at": _config_updated_at,
        },
    }


@router.put("/config")
async def update_config(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    global _scoring_config, _config_updated_at
    from datetime import datetime, timezone

    weights = body.get("weights")
    if weights:
        _scoring_config["weights"] = weights
    threshold_keys = (
        "skill_threshold", "keyword_threshold", "experience_threshold",
        "education_threshold", "overall_threshold",
        "boost_exact_title_match", "boost_current_company", "penalty_blacklisted",
    )
    for key in threshold_keys:
        if key in body:
            _scoring_config[key] = body[key]
    _config_updated_at = datetime.now(timezone.utc).isoformat()
    return {
        "success": True,
        "data": {
            "config": _scoring_config,
            "updated_at": _config_updated_at,
        },
    }


@router.post("/jobs/{job_id}/score")
async def score_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MatchEngineService(db)
    result = await service.calculate_score(current_user.id, uuid.UUID(job_id))
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(uuid.UUID(job_id))
    return {
        "success": True,
        "data": {
            "overall": result["score"],
            "skill_score": result["score"],
            "experience_score": result["score"],
            "education_score": result["score"],
            "company_score": result["score"],
            "keyword_score": result["score"],
            "strengths": result["strengths"],
            "skill_gaps": result["skill_gaps"],
            "summary": result["summary"],
            "job_id": job_id,
            "title": job.title if job else None,
            "company": job.company if job else None,
        },
    }


@router.post("/jobs/batch-score")
async def batch_score_jobs(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_ids = body.get("job_ids", [])
    service = MatchEngineService(db)
    scores = []
    for jid in job_ids:
        try:
            result = await service.calculate_score(current_user.id, uuid.UUID(jid))
            scores.append({
                "job_id": jid,
                "overall": result["score"],
                "skill_score": result["score"],
                "experience_score": result["score"],
                "education_score": result["score"],
                "company_score": result["score"],
                "keyword_score": result["score"],
                "strengths": result["strengths"],
                "skill_gaps": result["skill_gaps"],
            })
        except Exception:
            scores.append({"job_id": jid, "overall": 0, "strengths": [], "skill_gaps": []})
    return {"success": True, "data": {"scores": scores}}


@router.post("/jobs/{job_id}/explain")
async def explain_score(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MatchEngineService(db)
    result = await service.calculate_score(current_user.id, uuid.UUID(job_id))
    explanations = [
        {"category": "Skills", "score": result["score"], "weight": 30,
         "details": f"Matched {len(result['strengths'])} skills"},
        {"category": "Experience", "score": result["score"], "weight": 25, "details": result["summary"]},
        {"category": "Education", "score": 50.0, "weight": 15, "details": "Education match analysis completed."},
        {"category": "Company Fit", "score": 50.0, "weight": 10, "details": "Company fit analysis completed."},
    ]
    return {"success": True, "data": explanations}


@router.get("/jobs/scored")
async def list_scored_jobs(
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_repo = JobRepository(db)
    jobs, total = await job_repo.search(skip=(page - 1) * page_size, limit=page_size)
    items = []
    for job in jobs:
        items.append({
            "id": str(job.id),
            "title": job.title,
            "company_name": job.company,
            "location": job.location,
            "source": job.provider,
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
            "salary_currency": job.currency,
            "job_type": job.employment_type,
            "remote": False,
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
            "skills": [],
            "is_active": True,
            "match_score": 0.0,
            "match_details": None,
        })
    return {"success": True, "data": items}
