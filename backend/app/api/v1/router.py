from fastapi import APIRouter

from app.api.v1 import auth, jobs, portfolio, profile, resumes, users

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
    portfolio.router, prefix="/portfolio", tags=["Portfolio"]
)
api_router.include_router(
    jobs.router, prefix="/jobs", tags=["Jobs"]
)
