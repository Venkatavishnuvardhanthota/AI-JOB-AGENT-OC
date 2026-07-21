import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AuditRepository(session)

    async def log(
        self,
        event_type: str,
        user_id: uuid.UUID | None = None,
        entity: str | None = None,
        entity_id: uuid.UUID | None = None,
        outcome: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        await self.repo.log(
            event_type=event_type,
            user_id=str(user_id) if user_id else None,
            entity=entity,
            entity_id=str(entity_id) if entity_id else None,
            outcome=outcome,
            metadata=metadata,
        )
