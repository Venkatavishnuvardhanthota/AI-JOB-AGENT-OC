import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base


class Application(Base):
    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("application_runs.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="saved", nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    job_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "job_posting_id", name="uq_user_job_application"),
    )

    user = relationship("User", backref="applications")
    job_posting = relationship("JobPosting", backref="applications")
    run = relationship("ApplicationRun", backref="applications")
    notes = relationship("ApplicationNote", back_populates="application", cascade="all, delete-orphan")
    tag_mappings = relationship("ApplicationTagMapping", back_populates="application", cascade="all, delete-orphan")
    timeline_events = relationship("ApplicationTimelineEvent", back_populates="application", cascade="all, delete-orphan")


class ApplicationNote(Base):
    __tablename__ = "application_notes"

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    application = relationship("Application", back_populates="notes")


class ApplicationTag(Base):
    __tablename__ = "application_tags"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_tag_name"),
    )

    user = relationship("User", backref="application_tags")
    application_mappings = relationship("ApplicationTagMapping", back_populates="tag", cascade="all, delete-orphan")


class ApplicationTagMapping(Base):
    __tablename__ = "application_tag_mappings"

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("application_tags.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )

    application = relationship("Application", back_populates="tag_mappings")
    tag = relationship("ApplicationTag", back_populates="application_mappings")


class ApplicationTimelineEvent(Base):
    __tablename__ = "application_timeline_events"

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.now
    )

    application = relationship("Application", back_populates="timeline_events")
