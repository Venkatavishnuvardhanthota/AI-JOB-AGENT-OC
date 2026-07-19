import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base


class ApplicationSchedule(Base):
    __tablename__ = "application_schedules"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="stopped", nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)
    max_applications_per_day: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    days_of_week: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    time_of_day: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="application_schedules")
