from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import structlog

from app.ai.config import AIConfig
from app.ai.http_client import AIHTTPClient
from app.ai.interfaces import AIProvider
from app.ai.schemas import (
    AIRequest,
    AIResponse,
    CapabilityInfo,
    GenerationMetadata,
    ModelInfo,
    ProviderInfo,
    UsageMetrics,
)

logger = structlog.get_logger(__name__)


GEMINI_KNOWN_MODELS: list[dict[str, Any]] = [
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "tokens": 1048576,
     "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "tokens": 1048576,
     "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "tokens": 2097152,
     "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "tokens": 1048576,
     "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-1.5-flash-8b", "name": "Gemini 1.5 Flash-8B", "tokens": 1048576,
     "vision": True, "fc": True, "streaming": True},
]


class GeminiProvider(AIProvider):
    name = "gemini"
    display_name = "Gemini"
    description = "Google Gemini models"
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
            base_url=self.param("base_url", config.gemini_base_url),
            api_key=self.param("api_key", config.gemini_api_key),
            timeout_seconds=self.param("timeout_seconds", config.timeout_seconds),
            max_retries=self.param("max_retries", config.max_retries),
            retry_delay_seconds=self.param("retry_delay_seconds", config.retry_delay_seconds),
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if not self.param("api_key", self.config.gemini_api_key):
            errors.append("GEMINI_API_KEY is not set")
        return errors

    def _default_model(self) -> str:
        return self.param("default_model", self.config.gemini_default_model)

    def _build_url(self, model: str, action: str = "generateContent") -> str:
        key = self.param("api_key", self.config.gemini_api_key) or ""
        return f"/v1beta/models/{model}:{action}?key={key}"

    def _build_body(self, request: AIRequest, *, stream: bool = False) -> dict[str, Any]:
        body: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": request.prompt}]}],
        }
        if request.system_prompt:
            body["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}
        generation_config: dict[str, Any] = {}
        temperature = (
            request.temperature
            if request.temperature is not None
            else self.param("temperature", self.config.temperature)
        )
        if temperature is not None:
            generation_config["temperature"] = temperature
        max_tokens = (
            request.max_tokens
            if request.max_tokens is not None
            else self.param("max_tokens", self.config.max_tokens)
        )
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if request.stop_sequences:
            generation_config["stopSequences"] = request.stop_sequences
        if stream:
            generation_config["responseModalities"] = ["TEXT"]
        if generation_config:
            body["generationConfig"] = generation_config
        return body

    async def generate(self, request: AIRequest) -> AIResponse:
        body = self._build_body(request)
        model = request.model or self._default_model()
        url = self._build_url(model)
        response = await self._client.post(url, json=body)
        data = response.json()

        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            candidate = candidates[0]
            content_parts = candidate.get("content", {}).get("parts", [])
            for part in content_parts:
                content += part.get("text", "")
            finish_reason = candidate.get("finishReason", "stop")
        else:
            content = data.get("text", "")
            finish_reason = "stop"

        usage_data = data.get("usageMetadata", {})
        usage = UsageMetrics(
            prompt_tokens=usage_data.get("promptTokenCount"),
            completion_tokens=usage_data.get("candidatesTokenCount"),
            total_tokens=usage_data.get("totalTokenCount"),
        )

        metadata = GenerationMetadata(
            model=model,
            provider=self.name,
            finish_reason=finish_reason,
        )

        return AIResponse(
            content=content,
            model=model,
            provider=self.name,
            usage=usage,
            metadata=metadata,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        body = self._build_body(request, stream=True)
        model = request.model or self._default_model()
        url = self._build_url(model, "streamGenerateContent") + "&alt=sse"
        async for payload in self._client.stream(url, json=body):
            candidates = payload.get("candidates") or []
            if not candidates:
                continue
            content_parts = candidates[0].get("content", {}).get("parts", [])
            for part in content_parts:
                piece = part.get("text")
                if piece:
                    yield piece

    async def health_check(self) -> bool:
        try:
            url = self._build_url(self._default_model(), "generateContent")
            response = await self._client.post(
                url,
                json={"contents": [{"role": "user", "parts": [{"text": "ping"}]}]},
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
                supports_streaming=m.get("streaming", True),
                supports_function_calling=m.get("fc", False),
                supports_vision=m.get("vision", False),
                supports_json_mode=True,
            )
            for m in GEMINI_KNOWN_MODELS
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
            configured=bool(self.param("api_key", self.config.gemini_api_key)),
        )
