import logging

from app.schemas.llm import (
    LLMMessage,
    LLMRequest,
    RAGRequest,
    RAGResponse,
    VectorDocument,
)
from app.services.llm.embeddings import EmbeddingService
from app.services.llm.factory import get_llm_client
from app.services.llm.vector_store import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_RAG_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question based on the "
    "provided context. If the context does not contain enough information, "
    "say so clearly. Cite the source document IDs where relevant."
)


class RAGService:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService | None = None,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service or EmbeddingService()

    async def query(
        self,
        request: RAGRequest,
    ) -> RAGResponse:
        query_embedding_resp = await self.embedding_service.embed([request.query])
        query_embedding = query_embedding_resp.embeddings[0]

        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            min_score=request.min_score,
        )

        answer = await self._generate_answer(request, results)
        return RAGResponse(
            answer=answer,
            sources=results,
            model=query_embedding_resp.model,
            provider=query_embedding_resp.provider,
        )

    async def _generate_answer(
        self,
        request: RAGRequest,
        results: list[VectorDocument],
    ) -> str:
        client = get_llm_client()
        if not client:
            return "No LLM client available."

        context_parts = []
        for doc in results:
            context_parts.append(
                f"[Source: {doc.id}] {doc.content}"
            )
        context = "\n\n".join(context_parts) if context_parts else "No relevant context found."

        system_prompt = request.system_prompt or DEFAULT_RAG_SYSTEM_PROMPT
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(
                role="system",
                content=f"Context:\n{context}",
            ),
            LLMMessage(role="user", content=request.query),
        ]

        llm_request = LLMRequest(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
        )
        response = await client.complete(llm_request)
        return response.content
