from __future__ import annotations

from typing import Any

import structlog

from app.ai.config import AIConfig
from app.ai.http_client import AIHTTPClient
from app.ai.interfaces import AIProvider
from app.ai.schemas import AIRequest, AIResponse, CapabilityInfo, GenerationMetadata, ModelInfo, ProviderInfo, UsageMetrics

logger = structlog.get_logger(__name__)


GEMINI_KNOWN_MODELS: list[dict[str, Any]] = [
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "tokens": 1048576, "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "tokens": 1048576, "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "tokens": 2097152, "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "tokens": 1048576, "vision": True, "fc": True, "streaming": True},
    {"id": "gemini-1.5-flash-8b", "name": "Gemini 1.5 Flash-8B", "tokens": 1048576, "vision": True, "fc": True, "streaming": True},
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
            base_url=config.gemini_base_url,
            api_key=config.gemini_api_key,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if not self.config.gemini_api_key:
            errors.append("GEMINI_API_KEY is not set")
        return errors

    def _build_url(self, model: str, action: str = "generateContent") -> str:
        key = self.config.gemini_api_key or ""
        return f"/v1beta/models/{model}:{action}?key={key}"

    async def generate(self, request: AIRequest) -> AIResponse:
        contents: list[dict[str, Any]] = []
        if request.system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"[System: {request.system_prompt}]"}]})
        contents.append({"role": "user", "parts": [{"text": request.prompt}]})

        body: dict[str, Any] = {
            "contents": contents,
        }
        if request.temperature is not None:
            body.setdefault("generationConfig", {})["temperature"] = request.temperature
        if request.max_tokens is not None:
            body.setdefault("generationConfig", {})["maxOutputTokens"] = request.max_tokens
        if request.stop_sequences:
            body.setdefault("generationConfig", {})["stopSequences"] = request.stop_sequences

        url = self._build_url(request.model or self.config.gemini_default_model)
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
            model=request.model or self.config.gemini_default_model,
            provider=self.name,
            finish_reason=finish_reason,
        )

        return AIResponse(
            content=content,
            model=request.model or self.config.gemini_default_model,
            provider=self.name,
            usage=usage,
            metadata=metadata,
        )

    async def health_check(self) -> bool:
        try:
            url = self._build_url(self.config.gemini_default_model, "generateContent")
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
            configured=bool(self.config.gemini_api_key),
        )
