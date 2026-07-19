from fastapi import APIRouter

from app.api.v1 import (
    auth,
    company_research,
    interview_prep,
    jobs,
    llm,
    matching,
    portfolio,
    profile,
    resume_optimizer,
    resumes,
    users,
)

api_router = APIRouter()

api_router.include_router(
    auth.router, prefix="/auth", tags=["Authentication"]
)
api_router.include_router(
    users.router, prefix="/users", tags=["Users"]
)
api_router.include_router(
    profile.router, prefix="/profile", tags=["Profile"]
)
api_router.include_router(
    resumes.router, prefix="/resumes", tags=["Resumes"]
)
api_router.include_router(
    resume_optimizer.router, prefix="/resumes", tags=["Resumes"]
)
api_router.include_router(
    portfolio.router, prefix="/portfolio", tags=["Portfolio"]
)
api_router.include_router(
    jobs.router, prefix="/jobs", tags=["Jobs"]
)
api_router.include_router(
    matching.router, prefix="/matching", tags=["Matching"]
)
api_router.include_router(
    company_research.router, prefix="/company", tags=["Company Research"]
)
api_router.include_router(
    interview_prep.router, prefix="/company", tags=["Interview Preparation"]
)
api_router.include_router(
    llm.router, prefix="/llm", tags=["LLM"]
)
