from sqlalchemy import select

from database.models.ai_settings import AISettings
from database.repositories.base import BaseRepository


class AISettingsRepository(BaseRepository):
    model_class = AISettings

    async def get(self) -> AISettings | None:
        stmt = select(AISettings).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert(self, settings: AISettings) -> AISettings:
        existing = await self.get()
        if existing is None:
            self.session.add(settings)
            await self.session.flush()
            return settings
        existing.default_provider = settings.default_provider
        existing.default_model = settings.default_model
        existing.fallback_provider = settings.fallback_provider
        existing.fallback_model = settings.fallback_model
        existing.temperature = settings.temperature
        existing.max_tokens = settings.max_tokens
        existing.timeout_seconds = settings.timeout_seconds
        existing.max_retries = settings.max_retries
        existing.retry_delay_seconds = settings.retry_delay_seconds
        existing.streaming_enabled = settings.streaming_enabled
        existing.enabled_providers = settings.enabled_providers
        await self.session.flush()
        return existing
