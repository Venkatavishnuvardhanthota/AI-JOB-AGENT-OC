import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.career_profile import CareerProfile
from app.repositories.base import BaseRepository


class CareerProfileRepository(BaseRepository):
    model_class = CareerProfile

    async def get_by_user(self, user_id: uuid.UUID) -> CareerProfile | None:
        stmt = (
            select(CareerProfile)
            .where(CareerProfile.user_id == user_id)
            .options(
                joinedload(CareerProfile.education),
                joinedload(CareerProfile.experience),
                joinedload(CareerProfile.projects),
                joinedload(CareerProfile.skills),
                joinedload(CareerProfile.certifications),
                joinedload(CareerProfile.languages),
                joinedload(CareerProfile.preferences),
            )
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
