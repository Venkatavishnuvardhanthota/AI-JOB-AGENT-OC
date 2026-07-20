import uuid

from sqlalchemy import select

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    model_class = Notification

    async def list_by_user(self, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: uuid.UUID) -> Notification | None:
        notification = await self.get_by_id(notification_id)
        if notification:
            notification.is_read = True
            await self.session.flush()
        return notification
