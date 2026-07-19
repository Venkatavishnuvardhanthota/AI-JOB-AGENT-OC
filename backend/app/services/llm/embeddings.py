import logging

import httpx

from app.schemas.llm import EmbeddingResponse
from app.services.llm.config import llm_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.provider = provider or llm_config.embedding_provider
        self.model = model or llm_config.embedding_model
        self.api_key = api_key
        self.base_url = base_url
        self._client = httpx.AsyncClient(timeout=30)

    async def embed(self, texts: list[str]) -> EmbeddingResponse:
        if self.provider in ("openai", "openrouter"):
            return await self._embed_openai(texts)
        elif self.provider == "ollama":
            return await self._embed_ollama(texts)
        elif self.provider == "gemini":
            return await self._embed_gemini(texts)
        raise ValueError(f"Embedding not supported for provider: {self.provider}")

    async def _embed_openai(self, texts: list[str]) -> EmbeddingResponse:
        url = f"{(self.base_url or 'https://api.openai.com/v1').rstrip('/')}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {"model": self.model, "input": texts}
        resp = await self._client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        embeddings = [e["embedding"] for e in data["data"]]
        return EmbeddingResponse(
            embeddings=embeddings,
            model=data.get("model", self.model),
            provider=self.provider,
            dimension=len(embeddings[0]) if embeddings else 0,
        )

    async def _embed_ollama(self, texts: list[str]) -> EmbeddingResponse:
        url = f"{(self.base_url or 'http://localhost:11434').rstrip('/')}/api/embed"
        body = {"model": self.model, "input": texts}
        resp = await self._client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings", [])
        return EmbeddingResponse(
            embeddings=embeddings,
            model=data.get("model", self.model),
            provider=self.provider,
            dimension=len(embeddings[0]) if embeddings else 0,
        )

    async def _embed_gemini(self, texts: list[str]) -> EmbeddingResponse:
        model = self.model or "text-embedding-004"
        url = (
            f"{(self.base_url or 'https://generativelanguage.googleapis.com/v1beta').rstrip('/')}"
            f"/models/{model}:batchEmbedContents"
        )
        requests = [
            {"model": f"models/{model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        body = {"requests": requests}
        resp = await self._client.post(
            url, json=body, params={"key": self.api_key or ""}
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = [
            e["values"] for e in data.get("embeddings", [])
        ]
        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            provider=self.provider,
            dimension=len(embeddings[0]) if embeddings else 0,
        )

    async def close(self):
        await self._client.aclose()
