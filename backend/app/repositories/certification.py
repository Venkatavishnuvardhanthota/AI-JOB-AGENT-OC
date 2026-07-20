import uuid

from sqlalchemy import select

from app.models.certification import Certification
from app.repositories.base import BaseRepository


class CertificationRepository(BaseRepository):
    model_class = Certification

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[Certification]:
        stmt = (
            select(Certification)
            .where(Certification.profile_id == profile_id)
            .order_by(Certification.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
