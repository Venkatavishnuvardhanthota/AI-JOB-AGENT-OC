import uuid

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Language(Base):
    __tablename__ = "languages"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False)
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(100), nullable=True)

    profile = relationship("CareerProfile", back_populates="languages")

    __table_args__ = (
        Index("ix_languages_profile_id", "profile_id"),
        UniqueConstraint("profile_id", "language", name="uq_language_profile_language"),
    )
