import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.models.base import Base


class BrowserAutomationLog(Base):
    __tablename__ = "browser_automation_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    site_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_paths: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_consent_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_browser_logs_user_status", "user_id", "status"),
    )
