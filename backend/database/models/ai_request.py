import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class AIRequest(Base):
    __tablename__ = "ai_requests"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    user = relationship("User", back_populates="ai_requests")
    responses = relationship("AIResponse", back_populates="request", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_ai_requests_user_id", "user_id"),
        Index("ix_ai_requests_provider", "provider"),
        Index("ix_ai_requests_status", "status"),
    )
