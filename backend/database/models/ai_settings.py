import uuid

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class AISettings(Base):
    """Persisted global AI configuration (single row)."""

    __tablename__ = "ai_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    default_provider: Mapped[str] = mapped_column(String(50), default="openrouter", nullable=False)
    default_model: Mapped[str] = mapped_column(String(200), default="gpt-4o", nullable=False)
    fallback_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fallback_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    streaming_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled_providers: Mapped[str] = mapped_column(Text, default="openrouter", nullable=False)
