import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.models.career_profile import CareerProfile
from database.repositories.base import BaseRepository


class CareerProfileRepository(BaseRepository):
    model_class = CareerProfile

    async def get_by_user(self, user_id: uuid.UUID, load_relations: bool = False) -> CareerProfile | None:
        stmt = select(CareerProfile).where(CareerProfile.user_id == user_id)
        if load_relations:
            stmt = stmt.options(
                joinedload(CareerProfile.education),
                joinedload(CareerProfile.experience),
                joinedload(CareerProfile.projects),
                joinedload(CareerProfile.skills),
                joinedload(CareerProfile.certifications),
                joinedload(CareerProfile.languages),
                joinedload(CareerProfile.social_links),
                joinedload(CareerProfile.achievements),
                joinedload(CareerProfile.preferences),
            )
        result = await self.session.execute(stmt, execution_options={"populate_existing": True})
        return result.unique().scalar_one_or_none()
