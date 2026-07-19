import httpx

from app.schemas.llm import LLMRequest
from app.services.llm.base import BaseLLMClient


class AnthropicClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ):
        super().__init__(provider="anthropic", api_key=api_key)
        self.base_url = (
            base_url or "https://api.anthropic.com/v1"
        ).rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "x-api-key": api_key or "",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )

    async def _call_api(self, request: LLMRequest) -> dict:
        system = None
        messages = []
        for m in request.messages:
            if m.role == "system":
                system = m.content
            else:
                messages.append({"role": m.role, "content": m.content})
        body: dict = {
            "model": request.model or "claude-3-5-sonnet-latest",
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }
        if system:
            body["system"] = system
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.stop:
            body["stop_sequences"] = request.stop
        resp = await self._client.post("/messages", json=body)
        resp.raise_for_status()
        return resp.json()

    def _extract_content(self, data: dict) -> str:
        return data["content"][0]["text"]

    def _extract_model(self, data: dict) -> str:
        return data.get("model", "claude-3-5-sonnet-latest")

    async def close(self):
        await self._client.aclose()
