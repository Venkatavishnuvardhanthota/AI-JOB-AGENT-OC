import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    professional_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_years_experience: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    current_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    desired_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_salary: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    expected_salary: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    willing_to_relocate: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    visa_sponsorship_requirement: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notice_period: Mapped[str | None] = mapped_column(String(100), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_completeness: Mapped[int | None] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="profile")
    education = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="profile", cascade="all, delete-orphan")
    languages = relationship("Language", back_populates="profile", cascade="all, delete-orphan")
    social_links = relationship("SocialLink", back_populates="profile", cascade="all, delete-orphan")
    preferences = relationship("JobPreference", back_populates="profile", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (Index("ix_career_profiles_user_id", "user_id"),)
