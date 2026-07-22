from __future__ import annotations

from functools import lru_cache

from app.ai.config import AIConfig
from app.ai.registry import AIProviderRegistry
from app.ai.service import AIService


@lru_cache
def _get_registry() -> AIProviderRegistry:
    return AIProviderRegistry()


@lru_cache
def _get_config() -> AIConfig:
    from app.core.config import settings
    return AIConfig(
        default_provider=settings.AI_DEFAULT_PROVIDER,
        default_model=settings.AI_DEFAULT_MODEL,
        fallback_model=settings.AI_FALLBACK_MODEL,
        max_retries=settings.AI_MAX_RETRIES,
        timeout_seconds=settings.AI_TIMEOUT_SECONDS,
        temperature=settings.AI_TEMPERATURE,
        max_tokens=settings.AI_MAX_TOKENS,
        enabled_providers=settings.ENABLED_JOB_PROVIDERS,
    )


def get_registry() -> AIProviderRegistry:
    return _get_registry()


def get_ai_config() -> AIConfig:
    return _get_config()


def get_ai_service() -> AIService:
    registry = _get_registry()
    config = _get_config()
    return AIService(registry=registry, config=config)
