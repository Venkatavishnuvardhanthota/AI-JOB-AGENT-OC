import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class UserAISettings(Base):
    __tablename__ = "user_ai_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    resume_strategy: Mapped[str] = mapped_column(String(20), default="tailor", nullable=False)
    save_generated_resumes: Mapped[str] = mapped_column(String(20), default="submitted_only", nullable=False)

    user = relationship("User", back_populates="ai_settings")
