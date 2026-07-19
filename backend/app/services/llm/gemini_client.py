import httpx

from app.schemas.llm import LLMRequest
from app.services.llm.base import BaseLLMClient


class GeminiClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ):
        super().__init__(provider="gemini", api_key=api_key)
        self.base_url = (
            base_url or "https://generativelanguage.googleapis.com/v1beta"
        ).rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def _call_api(self, request: LLMRequest) -> dict:
        contents = []
        system_instruction = None
        for m in request.messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})
        model = request.model or "gemini-2.0-flash"
        url = f"{self.base_url}/models/{model}:generateContent"
        body: dict = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": request.max_tokens or 4096,
            },
        }
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        if request.temperature is not None:
            body["generationConfig"]["temperature"] = request.temperature
        if request.stop:
            body["generationConfig"]["stopSequences"] = request.stop
        resp = await self._client.post(
            url, json=body, params={"key": self.api_key or ""}
        )
        resp.raise_for_status()
        return resp.json()

    def _extract_content(self, data: dict) -> str:
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _extract_model(self, data: dict) -> str:
        return data.get("modelVersion", "gemini-2.0-flash")

    async def close(self):
        await self._client.aclose()
