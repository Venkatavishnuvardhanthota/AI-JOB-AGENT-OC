import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Education(Base):
    __tablename__ = "education"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currently_studying: Mapped[bool | None] = mapped_column(Boolean, default=False)
    cgpa: Mapped[str | None] = mapped_column(String(20), nullable=True)

    profile = relationship("CareerProfile", back_populates="education")

    __table_args__ = (
        Index("ix_education_profile_id", "profile_id"),
        Index("ix_education_institution", "institution"),
    )
