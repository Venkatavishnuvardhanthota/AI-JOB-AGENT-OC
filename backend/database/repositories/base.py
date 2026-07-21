from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from database.base import Base


class BaseRepository:
    model_class: type[Base] = Base

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, model: Base) -> Base:
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def bulk_create(self, models: list[Base]) -> list[Base]:
        self.session.add_all(models)
        await self.session.flush()
        for m in models:
            await self.session.refresh(m)
        return models

    async def get_by_id(self, id: uuid.UUID) -> Base | None:
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: list | None = None,
        order_by: str | None = None,
        desc: bool = True,
    ) -> Sequence[Base]:
        stmt: Select = select(self.model_class)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        order_col = getattr(self.model_class, order_by, None) if order_by else self.model_class.created_at
        stmt = stmt.order_by(order_col.desc().nullslast() if desc else order_col.asc().nullslast())
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_all(
        self,
        *,
        filters: list | None = None,
        order_by: str | None = None,
        desc: bool = True,
    ) -> Sequence[Base]:
        stmt: Select = select(self.model_class)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        order_col = getattr(self.model_class, order_by, None) if order_by else self.model_class.created_at
        stmt = stmt.order_by(order_col.desc().nullslast() if desc else order_col.asc().nullslast())
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def update(self, model: Base) -> Base:
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def update_fields(self, id: uuid.UUID, **values) -> Base | None:
        stmt = sa_update(self.model_class).where(self.model_class.id == id).values(**values)
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get_by_id(id)

    async def delete(self, model: Base) -> None:
        await self.session.delete(model)
        await self.session.flush()

    async def delete_by_id(self, id: uuid.UUID) -> bool:
        stmt = sa_delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def soft_delete(self, id: uuid.UUID) -> Base | None:
        model = await self.get_by_id(id)
        if model:
            model.soft_delete()
            await self.session.flush()
        return model

    async def count(self, filters: list | None = None) -> int:
        stmt = select(func.count()).select_from(self.model_class)
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, **kwargs) -> bool:
        stmt = select(self.model_class)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model_class, key) == value)
        stmt = stmt.limit(1)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none() is not None

    async def paginate(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
        filters: list | None = None,
        order_by: str | None = None,
        desc: bool = True,
    ) -> dict:
        skip = (page - 1) * page_size
        items = await self.list(skip=skip, limit=page_size, filters=filters, order_by=order_by, desc=desc)
        total = await self.count(filters=filters)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        }
