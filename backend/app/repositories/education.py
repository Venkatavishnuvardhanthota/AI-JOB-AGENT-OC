import uuid

from sqlalchemy import select

from app.models.education import Education
from app.repositories.base import BaseRepository


class EducationRepository(BaseRepository):
    model_class = Education

    async def list_by_profile(self, profile_id: uuid.UUID) -> list[Education]:
        stmt = select(Education).where(Education.profile_id == profile_id).order_by(Education.start_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
