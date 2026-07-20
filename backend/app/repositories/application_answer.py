import uuid

from sqlalchemy import select

from app.models.application_answer import ApplicationAnswer
from app.repositories.base import BaseRepository


class ApplicationAnswerRepository(BaseRepository):
    model_class = ApplicationAnswer

    async def list_by_application(self, application_id: uuid.UUID) -> list[ApplicationAnswer]:
        stmt = select(ApplicationAnswer).where(ApplicationAnswer.application_id == application_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
