from __future__ import annotations

import structlog

from app.ai.config import AIConfig
from app.ai.exceptions import AIServiceValidationError, ProviderNotFoundError
from app.ai.registry import AIProviderRegistry
from app.ai.schemas import AIRequest, AIResponse, ProviderInfo

logger = structlog.get_logger(__name__)


class AIService:
    def __init__(self, registry: AIProviderRegistry, config: AIConfig) -> None:
        self._registry = registry
        self._config = config

    async def generate(self, request: AIRequest) -> AIResponse:
        provider_name = request.provider or self._config.default_provider
        model = request.model or self._config.default_model

        if not request.prompt.strip():
            raise AIServiceValidationError("Prompt must not be empty.")

        provider = self._registry.resolve(provider_name)

        resolved = AIRequest(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            model=model,
            temperature=request.temperature if request.temperature is not None else self._config.temperature,
            max_tokens=request.max_tokens if request.max_tokens is not None else self._config.max_tokens,
            provider=provider_name,
            stop_sequences=request.stop_sequences,
        )

        logger.info(
            "Generating AI content",
            provider=provider_name,
            model=model,
            prompt_length=len(resolved.prompt),
        )

        return await provider.generate(resolved)

    async def health_check(self, provider_name: str | None = None) -> dict[str, bool]:
        targets = [provider_name] if provider_name else self._registry.list_providers()
        results: dict[str, bool] = {}
        for name in targets:
            try:
                provider = self._registry.resolve(name)
                is_healthy = await provider.health_check()
                results[name] = is_healthy
            except ProviderNotFoundError:
                results[name] = False
            except Exception:
                logger.exception("Health check failed for provider", provider=name)
                results[name] = False
        return results

    async def available_models(self, provider_name: str | None = None) -> dict[str, list]:
        targets = [provider_name] if provider_name else self._registry.list_providers()
        results: dict[str, list] = {}
        for name in targets:
            try:
                provider = self._registry.resolve(name)
                models = await provider.available_models()
                results[name] = [m.model_dump() for m in models]
            except ProviderNotFoundError:
                results[name] = []
            except Exception:
                logger.exception("Failed to fetch models for provider", provider=name)
                results[name] = []
        return results

    async def provider_info(self, provider_name: str) -> ProviderInfo:
        provider = self._registry.resolve(provider_name)
        return await provider.provider_info()

    def list_providers(self) -> list[str]:
        return self._registry.list_providers()

    @property
    def config(self) -> AIConfig:
        return self._config
