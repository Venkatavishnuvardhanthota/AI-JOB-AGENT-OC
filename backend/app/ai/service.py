from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel

from app.ai.config import AIConfig
from app.ai.exceptions import (
    AIServiceValidationError,
    GenerationError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    TimeoutError,
)
from app.ai.prompts.parser import ResponseParser
from app.ai.prompts.renderer import PromptRenderer
from app.ai.registry import AIProviderRegistry
from app.ai.schemas import AIRequest, AIResponse, HealthCheckResult, ModelInfo, ProviderInfo

if TYPE_CHECKING:
    from app.ai.prompts.registry import PromptTemplateRegistry

logger = structlog.get_logger(__name__)

FALLBACK_ELIGIBLE = (TimeoutError, ProviderUnavailableError, GenerationError)


class AIService:
    def __init__(
        self,
        registry: AIProviderRegistry,
        config: AIConfig,
        prompt_registry: PromptTemplateRegistry | None = None,
    ) -> None:
        self._registry = registry
        self._config = config
        self._prompt_registry = prompt_registry
        self._renderer = PromptRenderer()
        self._parser = ResponseParser()

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

        logger.info(
            "AI request started",
            provider=provider_name,
            model=model,
            prompt_length=len(request.prompt),
            has_system_prompt=bool(request.system_prompt),
        )

        start = time.monotonic()
        try:
            response = await self._generate_with_fallback(resolved, provider_name)
            elapsed = (time.monotonic() - start) * 1000
            logger.info(
                "AI request completed",
                provider=response.provider,
                model=response.model,
                latency_ms=round(elapsed, 1),
                finish_reason=response.metadata.finish_reason if response.metadata else None,
                prompt_tokens=response.usage.prompt_tokens if response.usage else None,
                completion_tokens=response.usage.completion_tokens if response.usage else None,
            )
            return response
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                "AI request failed",
                provider=provider_name,
                model=model,
                latency_ms=round(elapsed, 1),
            )
            raise

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
                fallback_model = self._config.fallback_model if i > 0 else request.model
                resolved = request.model_copy(update={"provider": name, "model": fallback_model})

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

    async def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str | None = None,
    ) -> str:
        request = AIRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
        )
        response = await self.generate(request)
        return response.content

    async def generate_stream(
        self,
        request: AIRequest,
    ) -> AsyncIterator[str]:
        provider_name = request.provider or self._config.default_provider
        model = request.model or self._config.default_model
        resolved = request.model_copy(update={"provider": provider_name, "model": model})
        provider = self._registry.resolve(provider_name)
        async for chunk in provider.stream(resolved):
            yield chunk

    async def generate_prompted(
        self,
        template_name: str,
        variables: dict[str, str],
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str | None = None,
    ) -> AIResponse:
        if self._prompt_registry is None:
            raise GenerationError("Prompt registry is not configured on this AIService instance.")

        template = self._prompt_registry.get(template_name)
        rendered = self._renderer.render(template, variables)
        effective_system = system_prompt or template.system_prompt

        request = AIRequest(
            prompt=rendered,
            system_prompt=effective_system,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
        )

        logger.info(
            "Generating from prompt template",
            template=template_name,
            variables=list(variables.keys()),
        )

        return await self.generate(request)

    async def generate_structured(
        self,
        template_name: str,
        variables: dict[str, str],
        response_model: type[BaseModel],
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: str | None = None,
    ) -> BaseModel:
        response = await self.generate_prompted(
            template_name=template_name,
            variables=variables,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
        )

        return self._parser.parse(response.content, response_model)

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

    async def detailed_health(self, provider_name: str | None = None) -> list[HealthCheckResult]:
        targets = [provider_name] if provider_name else self._registry.list_providers()
        results: list[HealthCheckResult] = []
        for name in targets:
            try:
                provider = self._registry.resolve(name)
                start = time.monotonic()
                is_healthy = await provider.health_check()
                latency = (time.monotonic() - start) * 1000
                results.append(HealthCheckResult(
                    provider=name,
                    model=self._config.default_model,
                    healthy=is_healthy,
                    connected=is_healthy,
                    latency_ms=round(latency, 1),
                    available=is_healthy,
                    configured=self._is_configured(provider),
                    is_default=name == self._config.default_provider,
                ))
            except ProviderNotFoundError:
                results.append(HealthCheckResult(
                    provider=name,
                    healthy=False,
                    error="Provider not found in registry",
                ))
            except Exception as exc:
                results.append(HealthCheckResult(
                    provider=name,
                    healthy=False,
                    error=str(exc),
                ))
        return results

    def _is_configured(self, provider) -> bool:
        errors = provider.validate_config()
        return len(errors) == 0

    async def available_models(self, provider_name: str | None = None) -> list[ModelInfo]:
        targets = [provider_name] if provider_name else self._registry.list_providers()
        results: list[ModelInfo] = []
        for name in targets:
            try:
                provider = self._registry.resolve(name)
                models = await provider.available_models()
                results.extend(models)
            except ProviderNotFoundError:
                continue
            except Exception:
                logger.exception("Failed to fetch models for provider", provider=name)
        return results

    async def provider_info(self, provider_name: str) -> ProviderInfo:
        provider = self._registry.resolve(provider_name)
        return await provider.provider_info()

    async def all_provider_info(self) -> dict[str, ProviderInfo]:
        return await self._registry.get_all_provider_infos(self._config.default_provider)

    def list_providers(self) -> list[str]:
        return self._registry.list_providers()

    @property
    def config(self) -> AIConfig:
        return self._config
