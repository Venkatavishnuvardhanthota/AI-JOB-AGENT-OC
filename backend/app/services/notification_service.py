import logging
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        notification_type: str,
        title: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            is_read=False,
        )
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        logger.info("Created notification %s for user %s", notification.id, user_id)
        return notification

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(
        self,
        user_id: uuid.UUID,
        notification_ids: list[uuid.UUID],
    ) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def unread_count(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
