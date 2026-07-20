import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, model: Base) -> Base:
        self.session.add(model)
        await self.session.flush()
        return model

    async def get_by_id(self, id: uuid.UUID) -> Base | None:
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[Base]:
        stmt = select(self.model_class).offset(skip).limit(limit).order_by(self.model_class.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, model: Base) -> Base:
        await self.session.flush()
        return model

    async def delete(self, model: Base) -> None:
        await self.session.delete(model)
        await self.session.flush()

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model_class)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, **kwargs) -> bool:
        stmt = select(self.model_class)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model_class, key) == value)
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
