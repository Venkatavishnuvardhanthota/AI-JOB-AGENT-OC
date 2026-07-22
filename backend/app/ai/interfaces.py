from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.config import AIConfig
from app.ai.schemas import AIRequest, AIResponse, ModelInfo, ProviderInfo


class AIProvider(ABC):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"
    supports_streaming: bool = False

    def __init__(self, config: AIConfig) -> None:
        self.config = config

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    async def available_models(self) -> list[ModelInfo]:
        ...

    @abstractmethod
    async def provider_info(self) -> ProviderInfo:
        ...
