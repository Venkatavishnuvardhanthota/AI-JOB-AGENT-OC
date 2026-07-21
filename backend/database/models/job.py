from datetime import datetime

from sqlalchemy import DateTime, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Job(Base):
    __tablename__ = "jobs"

    company_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    application_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    applications = relationship("Application", back_populates="job")
    company_insights = relationship("CompanyInsight", back_populates="job", uselist=False, cascade="all, delete-orphan")
    cover_letters = relationship("CoverLetter", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("provider", "provider_job_id", name="uq_job_provider"),
        Index("ix_jobs_provider_posted_at", "provider", "posted_at"),
        Index("ix_jobs_location_employment_type", "location", "employment_type"),
        Index("ix_jobs_company_posted_at", "company", "posted_at"),
        Index("ix_jobs_posted_at_employment_type", "posted_at", "employment_type"),
        Index("ix_jobs_provider_company", "provider", "company"),
        Index("ix_jobs_title", "title"),
        Index("ix_jobs_location", "location"),
        Index("ix_jobs_employment_type", "employment_type"),
    )
