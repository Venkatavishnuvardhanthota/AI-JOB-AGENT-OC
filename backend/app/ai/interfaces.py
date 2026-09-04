from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from app.ai.config import AIConfig
from app.ai.schemas import AIRequest, AIResponse, CapabilityInfo, ModelInfo, ProviderInfo


class AIProvider(ABC):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"
    supports_streaming: bool = False

    def __init__(self, config: AIConfig) -> None:
        self.config = config

    def param(self, key: str, default: Any = None) -> Any:
        """Resolve a per-provider configuration parameter (DB/UI override first, env fallback)."""
        value = self.config.provider_param(self.name, key)
        return value if value is not None else default

    @property
    def capabilities(self) -> CapabilityInfo:
        return CapabilityInfo(
            chat=True,
            streaming=self.supports_streaming,
            system_prompt_support=True,
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        return errors

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse: ...

    async def stream(self, request: AIRequest) -> AsyncIterator[str]:
        """Stream a response chunk by chunk. Providers without streaming support
        fall back to a single-chunk generation."""
        if not self.supports_streaming:
            response = await self.generate(request)
            yield response.content
            return
        raise NotImplementedError(f"Provider '{self.name}' does not implement streaming")

    @abstractmethod
    async def health_check(self) -> bool: ...

    @abstractmethod
    async def available_models(self) -> list[ModelInfo]: ...

    @abstractmethod
    async def provider_info(self) -> ProviderInfo: ...
