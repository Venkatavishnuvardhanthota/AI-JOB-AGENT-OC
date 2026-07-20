import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification import NotificationRepository


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepository(session)

    async def list_notifications(self, user_id: uuid.UUID, unread_only: bool = False) -> list[Notification]:
        return await self.repo.list_by_user(user_id, unread_only=unread_only)

    async def create(
        self, user_id: uuid.UUID, title: str, message: str | None = None, notification_type: str | None = None
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )
        return await self.repo.create(notification)

    async def mark_read(self, notification_id: uuid.UUID) -> Notification | None:
        return await self.repo.mark_read(notification_id)
