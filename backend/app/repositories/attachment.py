import uuid

from sqlalchemy import select

from app.models.attachment import Attachment
from app.repositories.base import BaseRepository


class AttachmentRepository(BaseRepository):
    model_class = Attachment

    async def list_by_application(self, application_id: uuid.UUID) -> list[Attachment]:
        stmt = select(Attachment).where(Attachment.application_id == application_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
