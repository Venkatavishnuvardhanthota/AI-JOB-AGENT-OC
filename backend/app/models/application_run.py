import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base


class ApplicationRun(Base):
    __tablename__ = "application_runs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("application_schedules.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)

    __table_args__ = (
        Index("ix_runs_user_status", "user_id", "status"),
    )
    job_ids: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    applications_submitted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_jobs_target: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="application_runs")
    schedule = relationship("ApplicationSchedule", backref="application_runs")
