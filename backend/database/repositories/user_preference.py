import uuid

from sqlalchemy import select

from database.models.user_preference import UserPreference
from database.repositories.base import BaseRepository


class UserPreferenceRepository(BaseRepository):
    model_class = UserPreference

    async def get_by_user(self, user_id: uuid.UUID) -> UserPreference | None:
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
