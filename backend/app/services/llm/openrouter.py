import httpx

from app.schemas.llm import LLMRequest
from app.services.llm.base import BaseLLMClient


class OpenRouterClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ):
        super().__init__(provider="openrouter", api_key=api_key)
        self.base_url = (
            base_url or "https://openrouter.ai/api/v1"
        ).rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def _call_api(self, request: LLMRequest) -> dict:
        body = {
            "model": request.model or "openai/gpt-4o",
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.stop:
            body["stop"] = request.stop
        resp = await self._client.post("/chat/completions", json=body)
        resp.raise_for_status()
        return resp.json()

    def _extract_content(self, data: dict) -> str:
        return data["choices"][0]["message"]["content"]

    def _extract_model(self, data: dict) -> str:
        return data.get("model", "openai/gpt-4o")

    async def close(self):
        await self._client.aclose()
