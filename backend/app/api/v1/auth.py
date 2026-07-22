from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenRefreshRequest,
)
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.register(body.email, body.password, body.first_name, body.last_name)
    return {"success": True, "data": result, "message": "Account created successfully."}


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(body.email, body.password)
    return {"success": True, "data": result}


@router.post("/logout", status_code=204)
async def logout(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.logout(current_user.id)


@router.post("/refresh")
async def refresh(body: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.refresh_token(body.refresh_token)
    return {"success": True, "data": result}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user).model_dump(),
    }


@router.patch("/me")
async def update_me(
    body: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    user = await service.update_profile(current_user.id, first_name=body.first_name, last_name=body.last_name)
    return {"success": True, "data": UserResponse.model_validate(user).model_dump()}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    await service.change_password(current_user.id, body.current_password, body.new_password)
    return {"success": True, "message": "Password changed successfully."}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return {"success": True, "message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    return {"success": True, "message": "Password reset functionality coming soon."}


@router.delete("/me", status_code=204)
async def delete_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    await service.delete_account(current_user.id)
