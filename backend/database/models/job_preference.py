import uuid

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class JobPreference(Base):
    __tablename__ = "job_preferences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    preferred_titles: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    preferred_locations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    employment_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    work_modes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    minimum_salary: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    preferred_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    profile = relationship("CareerProfile", back_populates="preferences")
