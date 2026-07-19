import httpx

from app.schemas.llm import LLMRequest
from app.services.llm.base import BaseLLMClient


class OllamaClient(BaseLLMClient):
    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 120,
    ):
        super().__init__(provider="ollama")
        self.base_url = (
            base_url or "http://localhost:11434"
        ).rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

    async def _call_api(self, request: LLMRequest) -> dict:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        body: dict = {
            "model": request.model or "llama3.2",
            "messages": messages,
            "stream": False,
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.stop:
            body["stop"] = request.stop
        resp = await self._client.post("/api/chat", json=body)
        resp.raise_for_status()
        return resp.json()

    def _extract_content(self, data: dict) -> str:
        return data["message"]["content"]

    def _extract_model(self, data: dict) -> str:
        return data.get("model", "llama3.2")

    async def close(self):
        await self._client.aclose()
