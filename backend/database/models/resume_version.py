import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    template: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_for_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_resume_user_version"),
        Index("ix_resume_versions_user_id", "user_id"),
        Index("ix_resume_versions_user_id_created_at", "user_id", "created_at"),
        Index("ix_resume_versions_user_id_archived", "user_id", "archived"),
    )
