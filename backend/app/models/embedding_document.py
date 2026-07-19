from sqlalchemy import String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmbeddingDocument(Base):
    __tablename__ = "embedding_documents"

    document_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<EmbeddingDocument(id={self.id}, doc_id={self.document_id!r})>"
