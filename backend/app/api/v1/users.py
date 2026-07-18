import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_superuser, get_user_repository
from app.repositories.user import UserRepository
from app.schemas.user import UserListResponse, UserResponse, UserUpdate

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    repo: UserRepository = Depends(get_user_repository),
    _: ... = Depends(get_current_superuser),
) -> UserListResponse:
    items, total = await repo.list(skip=skip, limit=limit)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in items],
        total=total,
        page=(skip // limit) + 1 if limit else 1,
        page_size=limit,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    repo: UserRepository = Depends(get_user_repository),
    _: ... = Depends(get_current_superuser),
) -> UserResponse:
    user = await repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    request: UserUpdate,
    repo: UserRepository = Depends(get_user_repository),
    _: ... = Depends(get_current_superuser),
) -> UserResponse:
    update_data = request.model_dump(exclude_unset=True)
    if "password" in update_data:
        from app.core.security import get_password_hash
        update_data["hashed_password"] = get_password_hash(
            update_data.pop("password")
        )
    user = await repo.update(user_id, **update_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    repo: UserRepository = Depends(get_user_repository),
    _: ... = Depends(get_current_superuser),
) -> None:
    deleted = await repo.delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
