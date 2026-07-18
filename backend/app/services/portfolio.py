import logging
import uuid

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio_item import PortfolioItem
from app.repositories.base import BaseRepository
from app.services.storage import FileStorageService

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(PortfolioItem, session)
        self.storage = FileStorageService()

    async def list_items(self, user_id: uuid.UUID) -> list[PortfolioItem]:
        stmt = (
            select(PortfolioItem)
            .where(PortfolioItem.user_id == user_id)
            .order_by(PortfolioItem.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_item(self, item_id: uuid.UUID, user_id: uuid.UUID) -> PortfolioItem | None:
        stmt = select(PortfolioItem).where(
            PortfolioItem.id == item_id,
            PortfolioItem.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_item(self, user_id: uuid.UUID, **kwargs) -> PortfolioItem:
        return await self.repo.create(user_id=user_id, **kwargs)

    async def update_item(
        self, item_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> PortfolioItem | None:
        item = await self.get_item(item_id, user_id)
        if not item:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(item, key, value)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete_item(self, item_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        item = await self.get_item(item_id, user_id)
        if not item:
            return False
        if item.media_url:
            self.storage.delete(item.media_url)
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def upload_media(
        self, item_id: uuid.UUID, user_id: uuid.UUID, file: UploadFile
    ) -> PortfolioItem | None:
        item = await self.get_item(item_id, user_id)
        if not item:
            return None
        old_media = item.media_url
        subdir = f"users/{user_id}/portfolio"
        file_path = await self.storage.save(file, subdir)
        item.media_url = file_path
        await self.session.flush()
        await self.session.refresh(item)
        if old_media:
            self.storage.delete(old_media)
        return item
