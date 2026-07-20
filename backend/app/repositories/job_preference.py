import uuid

from sqlalchemy import select

from app.models.job_preference import JobPreference
from app.repositories.base import BaseRepository


class JobPreferenceRepository(BaseRepository):
    model_class = JobPreference

    async def get_by_profile(self, profile_id: uuid.UUID) -> JobPreference | None:
        stmt = select(JobPreference).where(JobPreference.profile_id == profile_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
