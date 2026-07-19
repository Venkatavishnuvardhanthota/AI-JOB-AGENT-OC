import logging
import math
from collections import OrderedDict

from app.schemas.llm import VectorDocument

logger = logging.getLogger(__name__)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    def __init__(self):
        self._documents: OrderedDict[str, VectorDocument] = OrderedDict()
        self._embeddings: dict[str, list[float]] = {}

    def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> None:
        doc = VectorDocument(id=doc_id, content=content, metadata=metadata)
        self._documents[doc_id] = doc
        self._embeddings[doc_id] = embedding

    def remove_document(self, doc_id: str) -> bool:
        self._documents.pop(doc_id, None)
        return self._embeddings.pop(doc_id, None) is not None

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        min_score: float = 0.0,
    ) -> list[VectorDocument]:
        scored: list[tuple[float, VectorDocument]] = []
        for doc_id, doc in self._documents.items():
            emb = self._embeddings.get(doc_id)
            if emb is None:
                continue
            score = cosine_similarity(query_embedding, emb)
            if score >= min_score:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = scored[:top_k]
        for score, doc in results:
            doc.score = round(score, 4)
        return [doc for _, doc in results]

    @property
    def size(self) -> int:
        return len(self._documents)

    def clear(self) -> None:
        self._documents.clear()
        self._embeddings.clear()
