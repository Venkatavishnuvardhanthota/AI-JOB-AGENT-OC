from __future__ import annotations

from typing import Any

import structlog

from app.ai.config import AIConfig
from app.ai.http_client import AIHTTPClient
from app.ai.interfaces import AIProvider
from app.ai.schemas import AIRequest, AIResponse, CapabilityInfo, GenerationMetadata, ModelInfo, ProviderInfo, UsageMetrics

logger = structlog.get_logger(__name__)

MESSAGES_ENDPOINT = "/v1/messages"


ANTHROPIC_KNOWN_MODELS: list[dict[str, Any]] = [
    {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "tokens": 200000, "vision": True, "reasoning": True, "fc": True},
    {"id": "claude-4-20250514", "name": "Claude 4", "tokens": 200000, "vision": True, "reasoning": True, "fc": True},
    {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "tokens": 200000, "vision": True, "fc": True},
    {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "tokens": 200000, "vision": True, "fc": True},
    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "tokens": 200000, "vision": True, "fc": True},
    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "tokens": 200000, "vision": True, "fc": True},
    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "tokens": 200000, "vision": True, "fc": True},
]


class AnthropicProvider(AIProvider):
    name = "anthropic"
    display_name = "Anthropic"
    description = "Anthropic Claude models"
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
            reasoning=True,
        )

    def __init__(self, config: AIConfig) -> None:
        super().__init__(config)
        self._client = AIHTTPClient(
            base_url=config.anthropic_base_url,
            api_key=config.anthropic_api_key,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            default_headers={"anthropic-version": "2023-06-01"},
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if not self.config.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is not set")
        return errors

    async def generate(self, request: AIRequest) -> AIResponse:
        body: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens or 4096,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system_prompt:
            body["system"] = request.system_prompt
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.stop_sequences:
            body["stop_sequences"] = request.stop_sequences

        response = await self._client.post(MESSAGES_ENDPOINT, json=body)
        data = response.json()

        content_blocks = data.get("content", [])
        content = ""
        for block in content_blocks:
            if block.get("type") == "text":
                content += block.get("text", "")

        finish_reason = data.get("stop_reason")
        if finish_reason == "end_turn":
            finish_reason = "stop"

        usage_data = data.get("usage", {})
        usage = UsageMetrics(
            prompt_tokens=usage_data.get("input_tokens"),
            completion_tokens=usage_data.get("output_tokens"),
            total_tokens=(usage_data.get("input_tokens", 0) or 0) + (usage_data.get("output_tokens", 0) or 0),
        )

        metadata = GenerationMetadata(
            model=data.get("model", request.model),
            provider=self.name,
            finish_reason=finish_reason,
            id=data.get("id"),
        )

        return AIResponse(
            content=content,
            model=data.get("model", request.model) or request.model,
            provider=self.name,
            usage=usage,
            metadata=metadata,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.post(
                MESSAGES_ENDPOINT,
                json={
                    "model": self.config.anthropic_default_model,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
            )
            return response.status_code == 200
        except Exception:
            return False

    async def available_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                provider=self.name,
                description=None,
                max_tokens=m["tokens"],
                supports_streaming=True,
                supports_function_calling=m.get("fc", False),
                supports_vision=m.get("vision", False),
                supports_json_mode=True,
                supports_reasoning=m.get("reasoning", False),
            )
            for m in ANTHROPIC_KNOWN_MODELS
        ]

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
            configured=bool(self.config.anthropic_api_key),
        )
