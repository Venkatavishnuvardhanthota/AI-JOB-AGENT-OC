from __future__ import annotations

from typing import Any

import structlog

from app.ai.config import AIConfig
from app.ai.http_client import AIHTTPClient
from app.ai.interfaces import AIProvider
from app.ai.schemas import AIRequest, AIResponse, GenerationMetadata, ModelInfo, ProviderInfo, UsageMetrics

logger = structlog.get_logger(__name__)

OPENROUTER_CHAT_ENDPOINT = "/api/v1/chat/completions"
OPENROUTER_MODELS_ENDPOINT = "/api/v1/models"
OPENROUTER_KEY_ENDPOINT = "/api/v1/auth/key"


class OpenRouterProvider(AIProvider):
    name = "openrouter"
    display_name = "OpenRouter"
    description = "OpenRouter multi-provider AI gateway"
    version = "1.0.0"
    supports_streaming = True

    def __init__(self, config: AIConfig) -> None:
        super().__init__(config)
        self._client = AIHTTPClient(
            base_url=config.openrouter_base_url,
            api_key=config.openrouter_api_key,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    async def generate(self, request: AIRequest) -> AIResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        body: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.stop_sequences:
            body["stop"] = request.stop_sequences

        response = await self._client.post(OPENROUTER_CHAT_ENDPOINT, json=body)

        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        content = message.get("content", "")
        finish_reason = choice.get("finish_reason")

        usage_data = data.get("usage", {})
        usage = UsageMetrics(
            prompt_tokens=usage_data.get("prompt_tokens"),
            completion_tokens=usage_data.get("completion_tokens"),
            total_tokens=usage_data.get("total_tokens"),
        )

        metadata = GenerationMetadata(
            model=data.get("model", request.model),
            provider=self.name,
            finish_reason=finish_reason,
            id=data.get("id"),
        )

        return AIResponse(
            content=content,
            model=data.get("model", request.model),
            provider=self.name,
            usage=usage,
            metadata=metadata,
        )

    async def health_check(self) -> bool:
        try:
            await self._client.get(OPENROUTER_KEY_ENDPOINT, retry_on=set())
            return True
        except Exception:
            return False

    async def available_models(self) -> list[ModelInfo]:
        try:
            response = await self._client.get(OPENROUTER_MODELS_ENDPOINT)
            data = response.json()
            models = []
            for item in data.get("data", []):
                models.append(
                    ModelInfo(
                        id=item["id"],
                        name=item.get("name", item["id"]),
                        provider=self.name,
                        description=item.get("description"),
                        max_tokens=item.get("context_length"),
                        supports_streaming=True,
                        supports_vision="vision" in item.get("id", "").lower(),
                    )
                )
            return models
        except Exception:
            logger.exception("Failed to fetch models from OpenRouter")
            return []

    async def provider_info(self) -> ProviderInfo:
        models = await self.available_models()
        health = await self.health_check()
        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            models=models,
            is_available=health,
            version=self.version,
            supports_streaming=self.supports_streaming,
        )
