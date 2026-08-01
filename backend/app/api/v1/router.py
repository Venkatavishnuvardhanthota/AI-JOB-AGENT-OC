from fastapi import APIRouter

from app.api.v1 import (
    ai,
    ai_features,
    applications,
    auth,
    cover_letters,
    jobs,
    matching,
    profile,
    resume_strategy,
    resumes,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["Career Profile"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(cover_letters.router, prefix="/cover-letters", tags=["Cover Letters"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(matching.router, prefix="/matching", tags=["Matching"])
api_router.include_router(applications.router, prefix="/applications", tags=["Applications"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
api_router.include_router(ai_features.router, prefix="/ai", tags=["AI Features"])
api_router.include_router(resume_strategy.router, prefix="/ai", tags=["AI Features"])
