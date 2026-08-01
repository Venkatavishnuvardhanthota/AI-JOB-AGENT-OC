from __future__ import annotations

from typing import Any

import structlog

from app.ai.config import AIConfig
from app.ai.http_client import AIHTTPClient
from app.ai.interfaces import AIProvider
from app.ai.schemas import AIRequest, AIResponse, CapabilityInfo, GenerationMetadata, ModelInfo, ProviderInfo, UsageMetrics

logger = structlog.get_logger(__name__)

CHAT_ENDPOINT = "/v1/chat/completions"
MODELS_ENDPOINT = "/v1/models"


class OpenAIProvider(AIProvider):
    name = "openai"
    display_name = "OpenAI"
    description = "OpenAI GPT models (GPT-4o, GPT-4, GPT-3.5)"
    version = "1.0.0"
    supports_streaming = True

    @property
    def capabilities(self) -> CapabilityInfo:
        return CapabilityInfo(
            chat=True,
            streaming=True,
            vision=True,
            json_mode=True,
            function_calling=True,
            tool_calling=True,
            system_prompt_support=True,
            structured_output=True,
        )

    def __init__(self, config: AIConfig) -> None:
        super().__init__(config)
        self._client = AIHTTPClient(
            base_url=config.openai_base_url,
            api_key=config.openai_api_key,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if not self.config.openai_api_key:
            errors.append("OPENAI_API_KEY is not set")
        return errors

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

        response = await self._client.post(CHAT_ENDPOINT, json=body)

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
            await self._client.get(MODELS_ENDPOINT, retry_on=set())
            return True
        except Exception:
            return False

    async def available_models(self) -> list[ModelInfo]:
        try:
            response = await self._client.get(MODELS_ENDPOINT)
            data = response.json()
            models = []
            for item in data.get("data", []):
                model_id = item["id"]
                models.append(
                    ModelInfo(
                        id=model_id,
                        name=model_id,
                        provider=self.name,
                        description=None,
                        max_tokens=None,
                        supports_streaming=True,
                        supports_function_calling="gpt" in model_id and "instruct" not in model_id,
                        supports_vision="vision" in model_id or "gpt-4o" in model_id,
                        supports_json_mode="gpt-4" in model_id or "gpt-3.5" in model_id,
                        supports_reasoning="o1" in model_id or "o3" in model_id,
                    )
                )
            return models
        except Exception:
            logger.exception("Failed to fetch models from OpenAI")
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
            capabilities=self.capabilities,
            configured=bool(self.config.openai_api_key),
        )
