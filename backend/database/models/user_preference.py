import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    theme: Mapped[str | None] = mapped_column(String(50), default="light")
    language: Mapped[str | None] = mapped_column(String(10), default="en")
    notification_settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    search_defaults: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user = relationship("User", back_populates="preferences")
