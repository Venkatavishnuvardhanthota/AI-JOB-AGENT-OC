import uuid

from sqlalchemy import select

from database.models.ai_response import AIResponse
from database.repositories.base import BaseRepository


class AIResponseRepository(BaseRepository):
    model_class = AIResponse

    async def list_by_request(self, request_id: uuid.UUID) -> list[AIResponse]:
        stmt = select(AIResponse).where(AIResponse.request_id == request_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
