import uuid

from sqlalchemy import select

from database.models.user_ai_settings import UserAISettings
from database.repositories.base import BaseRepository


class UserAISettingsRepository(BaseRepository):
    model_class = UserAISettings

    async def get_by_user(self, user_id: uuid.UUID) -> UserAISettings | None:
        stmt = select(UserAISettings).where(UserAISettings.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID) -> UserAISettings:
        settings = await self.get_by_user(user_id)
        if settings is None:
            settings = UserAISettings(
                user_id=user_id,
                resume_strategy="tailor",
                save_generated_resumes="submitted_only",
            )
            await self.create(settings)
        return settings
