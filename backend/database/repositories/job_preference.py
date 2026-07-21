import uuid

from sqlalchemy import select

from database.models.job_preference import JobPreference
from database.repositories.base import BaseRepository


class JobPreferenceRepository(BaseRepository):
    model_class = JobPreference

    async def get_by_profile(self, profile_id: uuid.UUID) -> JobPreference | None:
        stmt = select(JobPreference).where(JobPreference.profile_id == profile_id)
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
