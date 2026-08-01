import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models import UserAISettings
from app.repositories import UserAISettingsRepository
from app.schemas.resume_strategy import (
    DEFAULT_RESUME_STRATEGY,
    DEFAULT_SAVE_GENERATED_RESUMES,
    VALID_RESUME_STRATEGIES,
    VALID_SAVE_GENERATED_RESUMES,
)


class AISettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings_repo = UserAISettingsRepository(session)

    async def get_settings(self, user_id: uuid.UUID) -> UserAISettings:
        return await self.settings_repo.get_or_create(user_id)

    async def update_settings(
        self,
        user_id: uuid.UUID,
        resume_strategy: str | None = None,
        save_generated_resumes: str | None = None,
    ) -> UserAISettings:
        settings = await self.settings_repo.get_or_create(user_id)

        if resume_strategy is not None:
            if resume_strategy not in VALID_RESUME_STRATEGIES:
                raise ValidationError(
                    "Invalid resume strategy.",
                    details={
                        "resume_strategy": resume_strategy,
                        "allowed": sorted(VALID_RESUME_STRATEGIES),
                    },
                )
            settings.resume_strategy = resume_strategy

        if save_generated_resumes is not None:
            if save_generated_resumes not in VALID_SAVE_GENERATED_RESUMES:
                raise ValidationError(
                    "Invalid save generated resumes option.",
                    details={
                        "save_generated_resumes": save_generated_resumes,
                        "allowed": sorted(VALID_SAVE_GENERATED_RESUMES),
                    },
                )
            settings.save_generated_resumes = save_generated_resumes

        await self.settings_repo.update(settings)
        return settings

    @staticmethod
    def defaults() -> dict:
        return {
            "resume_strategy": DEFAULT_RESUME_STRATEGY,
            "save_generated_resumes": DEFAULT_SAVE_GENERATED_RESUMES,
        }
