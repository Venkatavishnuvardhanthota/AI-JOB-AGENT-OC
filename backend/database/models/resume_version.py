import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    resume_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True
    )
    generated_for_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    origin: Mapped[str] = mapped_column(String(20), default="master", nullable=False)
    parent_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True
    )
    generation_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="resumes")
    applications = relationship(
        "Application", back_populates="resume", foreign_keys="Application.resume_id"
    )
    generated_for_applications = relationship(
        "Application",
        back_populates="generated_resume",
        foreign_keys="Application.generated_resume_id",
    )
    original_for_applications = relationship(
        "Application",
        back_populates="original_resume",
        foreign_keys="Application.original_resume_id",
    )
    sections = relationship(
        "ResumeSection", back_populates="resume", cascade="all, delete-orphan", order_by="ResumeSection.sort_order"
    )
    previous_version = relationship(
        "ResumeVersion",
        remote_side="ResumeVersion.id",
        foreign_keys=[previous_version_id],
        back_populates="next_versions",
    )
    next_versions = relationship(
        "ResumeVersion",
        remote_side="ResumeVersion.previous_version_id",
        foreign_keys=[previous_version_id],
        back_populates="previous_version",
    )
    parent_resume = relationship(
        "ResumeVersion",
        remote_side="ResumeVersion.id",
        foreign_keys=[parent_resume_id],
        back_populates="generated_resumes",
    )
    generated_resumes = relationship(
        "ResumeVersion",
        remote_side="ResumeVersion.parent_resume_id",
        foreign_keys=[parent_resume_id],
        back_populates="parent_resume",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_resume_user_version"),
        Index("ix_resume_versions_user_id", "user_id"),
        Index("ix_resume_versions_user_id_created_at", "user_id", "created_at"),
        Index("ix_resume_versions_user_id_archived", "user_id", "archived"),
        Index("ix_resume_versions_user_id_default", "user_id", "is_default"),
        Index("ix_resume_versions_user_id_origin", "user_id", "origin"),
        Index("ix_resume_versions_user_id_job_origin", "user_id", "generated_for_job_id", "origin"),
        Index("ix_resume_versions_status", "status"),
    )
