import uuid

from sqlalchemy import select

from database.models.application_event import ApplicationEvent
from database.repositories.base import BaseRepository


class ApplicationEventRepository(BaseRepository):
    model_class = ApplicationEvent

    async def list_by_application(self, application_id: uuid.UUID) -> list[ApplicationEvent]:
        stmt = (
            select(ApplicationEvent)
            .where(ApplicationEvent.application_id == application_id)
            .order_by(ApplicationEvent.occurred_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
