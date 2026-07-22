from __future__ import annotations

import structlog

from app.ai.config import AIConfig
from app.ai.exceptions import (
    AIServiceValidationError,
    GenerationError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    TimeoutError,
)
from app.ai.registry import AIProviderRegistry
from app.ai.schemas import AIRequest, AIResponse, ProviderInfo

logger = structlog.get_logger(__name__)

FALLBACK_ELIGIBLE = (TimeoutError, ProviderUnavailableError, GenerationError)


class AIService:
    def __init__(self, registry: AIProviderRegistry, config: AIConfig) -> None:
        self._registry = registry
        self._config = config

    async def generate(self, request: AIRequest) -> AIResponse:
        provider_name = request.provider or self._config.default_provider
        model = request.model or self._config.default_model

        if not request.prompt.strip():
            raise AIServiceValidationError("Prompt must not be empty.")

        resolved = AIRequest(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            model=model,
            temperature=request.temperature if request.temperature is not None else self._config.temperature,
            max_tokens=request.max_tokens if request.max_tokens is not None else self._config.max_tokens,
            provider=provider_name,
            stop_sequences=request.stop_sequences,
        )

        return await self._generate_with_fallback(resolved, provider_name)

    async def _generate_with_fallback(self, request: AIRequest, primary_provider: str) -> AIResponse:
        providers_to_try = [primary_provider]

        if primary_provider == self._config.default_provider:
            fallback_name = self._config.fallback_provider
            if fallback_name and fallback_name != primary_provider:
                providers_to_try.append(fallback_name)

        last_error: Exception | None = None
        for i, name in enumerate(providers_to_try):
            try:
                provider = self._registry.resolve(name)
                resolved = request.model_copy(update={"provider": name})

                logger.info(
                    "Generating AI content",
                    provider=name,
                    model=resolved.model,
                    prompt_length=len(resolved.prompt),
                    attempt=i + 1,
                    total=len(providers_to_try),
                )

                response = await provider.generate(resolved)
                if i > 0:
                    logger.info("Fallback succeeded", from_provider=providers_to_try[0], to_provider=name)
                return response
            except FALLBACK_ELIGIBLE as exc:
                last_error = exc
                logger.warning(
                    "Provider failed, trying fallback" if i < len(providers_to_try) - 1 else "All providers failed",
                    provider=name,
                    error=str(exc),
                    attempt=i + 1,
                )
                continue

        raise last_error or ProviderUnavailableError("All providers failed to generate content")

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
