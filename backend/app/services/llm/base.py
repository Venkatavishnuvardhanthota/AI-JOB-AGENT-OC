import logging
import time
from abc import ABC, abstractmethod

from app.schemas.llm import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    def __init__(self, provider: str, api_key: str | None = None):
        self.provider = provider
        self.api_key = api_key

    @abstractmethod
    async def _call_api(self, request: LLMRequest) -> dict:
        ...

    async def complete(self, request: LLMRequest) -> LLMResponse:
        start = time.monotonic()
        try:
            data = await self._call_api(request)
            latency = (time.monotonic() - start) * 1000
            return self._parse_response(data, latency)
        except Exception as e:
            logger.error(
                "LLM call failed",
                provider=self.provider,
                model=request.model,
                error=str(e),
            )
            raise

    def _parse_response(self, data: dict, latency_ms: float) -> LLMResponse:
        return LLMResponse(
            content=self._extract_content(data),
            model=self._extract_model(data),
            provider=self.provider,
            usage=self._extract_usage(data),
            latency_ms=round(latency_ms, 1),
        )

    @abstractmethod
    def _extract_content(self, data: dict) -> str:
        ...

    @abstractmethod
    def _extract_model(self, data: dict) -> str:
        ...

    def _extract_usage(self, data: dict) -> dict | None:
        usage = data.get("usage", data.get("usage_metadata"))
        if usage:
            return {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
        return None
