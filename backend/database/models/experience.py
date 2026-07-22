import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Experience(Base):
    __tablename__ = "experience"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currently_working: Mapped[bool | None] = mapped_column(Boolean, default=False)
    responsibilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    achievements: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    technologies_used: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile = relationship("CareerProfile", back_populates="experience")

    __table_args__ = (
        Index("ix_experience_profile_id", "profile_id"),
        Index("ix_experience_company", "company"),
    )
