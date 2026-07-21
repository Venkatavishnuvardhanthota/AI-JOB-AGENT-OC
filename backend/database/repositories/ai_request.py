import uuid

from sqlalchemy import select

from database.models.ai_request import AIRequest
from database.repositories.base import BaseRepository


class AIRequestRepository(BaseRepository):
    model_class = AIRequest

    async def list_by_user(self, user_id: uuid.UUID, skip: int = 0, limit: int = 50) -> list[AIRequest]:
        stmt = (
            select(AIRequest)
            .where(AIRequest.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(AIRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
