import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Any)


class BaseService(Generic[ModelType]):
    def __init__(self, repository: BaseRepository[ModelType]):
        self.repository = repository

    async def get(self, id: uuid.UUID) -> ModelType | None:
        return await self.repository.get(id)

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: list[Any] | None = None,
        order_by: Any | None = None,
    ) -> tuple[Sequence[ModelType], int]:
        return await self.repository.list(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by=order_by,
        )

    async def create(self, **kwargs: Any) -> ModelType:
        return await self.repository.create(**kwargs)

    async def update(
        self, id: uuid.UUID, **kwargs: Any
    ) -> ModelType | None:
        return await self.repository.update(id, **kwargs)

    async def delete(self, id: uuid.UUID) -> bool:
        return await self.repository.delete(id)
