import uuid

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Skill(Base):
    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_experience: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)

    profile = relationship("CareerProfile", back_populates="skills")

    __table_args__ = (UniqueConstraint("profile_id", "name", name="uq_skill_profile_name"),)
