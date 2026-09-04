import uuid

from sqlalchemy import select

from database.models.certification import Certification
from database.repositories.base import BaseRepository


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

    async def exists_by_name(self, profile_id: uuid.UUID, name: str) -> bool:
        stmt = select(Certification).where(
            Certification.profile_id == profile_id,
            Certification.name.ilike(name),
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none() is not None
