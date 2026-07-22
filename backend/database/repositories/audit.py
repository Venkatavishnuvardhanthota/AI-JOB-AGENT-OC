import uuid

from sqlalchemy import select

from database.models.audit_log import AuditLog
from database.repositories.base import BaseRepository


class AuditRepository(BaseRepository):
    model_class = AuditLog

    async def log(
        self,
        event_type: str,
        user_id: uuid.UUID | None = None,
        entity: str | None = None,
        entity_id: str | None = None,
        outcome: str | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        log_entry = AuditLog(
            user_id=user_id,
            event_type=event_type,
            entity=entity,
            entity_id=entity_id,
            outcome=outcome,
            details=details,
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry

    async def search(
        self,
        event_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = select(AuditLog)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        stmt = stmt.offset(skip).limit(limit).order_by(AuditLog.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
