from fastapi import APIRouter

from app.api.v1 import auth, profile, users

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
