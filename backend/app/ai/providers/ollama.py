from __future__ import annotations

from typing import Any

import structlog

from app.ai.config import AIConfig
from app.ai.http_client import AIHTTPClient
from app.ai.interfaces import AIProvider
from app.ai.schemas import AIRequest, AIResponse, GenerationMetadata, ModelInfo, ProviderInfo, UsageMetrics

logger = structlog.get_logger(__name__)

OLLAMA_CHAT_ENDPOINT = "/api/chat"
OLLAMA_TAGS_ENDPOINT = "/api/tags"


class OllamaProvider(AIProvider):
    name = "ollama"
    display_name = "Ollama"
    description = "Local Ollama server"
    version = "1.0.0"
    supports_streaming = False

    def __init__(self, config: AIConfig) -> None:
        super().__init__(config)
        self._client = AIHTTPClient(
            base_url=config.ollama_base_url,
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
            "stream": False,
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.stop_sequences:
            body["stop"] = request.stop_sequences

        response = await self._client.post(OLLAMA_CHAT_ENDPOINT, json=body)
        data = response.json()

        content = data.get("message", {}).get("content", "")
        finish_reason = data.get("done_reason", "stop") if data.get("done") else None

        metadata = GenerationMetadata(
            model=request.model,
            provider=self.name,
            finish_reason=finish_reason,
            duration_ms=int(data.get("total_duration", 0) / 1_000_000) if data.get("total_duration") else None,
        )

        if data.get("eval_count") is not None:
            usage = UsageMetrics(
                prompt_tokens=data.get("prompt_eval_count"),
                completion_tokens=data.get("eval_count"),
                total_tokens=(data.get("prompt_eval_count", 0) or 0) + (data.get("eval_count", 0) or 0),
            )
        else:
            usage = UsageMetrics()

        return AIResponse(
            content=content,
            model=request.model,
            provider=self.name,
            usage=usage,
            metadata=metadata,
        )

    async def health_check(self) -> bool:
        try:
            await self._client.get(OLLAMA_TAGS_ENDPOINT, retry_on=set())
            return True
        except Exception:
            return False

    async def available_models(self) -> list[ModelInfo]:
        try:
            response = await self._client.get(OLLAMA_TAGS_ENDPOINT)
            data = response.json()
            models = []
            for item in data.get("models", []):
                details = item.get("details", {})
                model_id = item["name"]
                models.append(
                    ModelInfo(
                        id=model_id,
                        name=model_id,
                        provider=self.name,
                        description=f"Ollama model: {model_id}",
                        max_tokens=None,
                        supports_streaming=False,
                        supports_function_calling=details.get("family") in ("llama", "mistral", "qwen2"),
                    )
                )
            return models
        except Exception:
            logger.exception("Failed to fetch models from Ollama")
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
