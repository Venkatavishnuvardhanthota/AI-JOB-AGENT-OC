import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioItemCreate,
    PortfolioItemResponse,
    PortfolioItemUpdate,
)
from app.services.portfolio import PortfolioService

router = APIRouter()


def get_portfolio_service(db: AsyncSession = Depends(get_db)) -> PortfolioService:
    return PortfolioService(db)


@router.get("", response_model=list[PortfolioItemResponse])
async def list_portfolio(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> list[PortfolioItemResponse]:
    items = await service.list_items(current_user.id)
    return [PortfolioItemResponse.model_validate(i) for i in items]


@router.post("", response_model=PortfolioItemResponse, status_code=201)
async def create_portfolio_item(
    request: PortfolioItemCreate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioItemResponse:
    item = await service.create_item(
        user_id=current_user.id, **request.model_dump()
    )
    return PortfolioItemResponse.model_validate(item)


@router.get("/{item_id}", response_model=PortfolioItemResponse)
async def get_portfolio_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioItemResponse:
    item = await service.get_item(item_id, current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found.")
    return PortfolioItemResponse.model_validate(item)


@router.put("/{item_id}", response_model=PortfolioItemResponse)
async def update_portfolio_item(
    item_id: uuid.UUID,
    request: PortfolioItemUpdate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioItemResponse:
    item = await service.update_item(
        item_id, current_user.id, **request.model_dump(exclude_unset=True)
    )
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found.")
    return PortfolioItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=204)
async def delete_portfolio_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> None:
    deleted = await service.delete_item(item_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Portfolio item not found.")


@router.post("/{item_id}/media", response_model=PortfolioItemResponse)
async def upload_portfolio_media(
    item_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioItemResponse:
    item = await service.upload_media(item_id, current_user.id, file)
    if not item:
        raise HTTPException(status_code=404, detail="Portfolio item not found.")
    return PortfolioItemResponse.model_validate(item)
