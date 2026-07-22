import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class ResumeSection(Base):
    __tablename__ = "resume_sections"

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False
    )
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    resume = relationship("ResumeVersion", back_populates="sections")

    __table_args__ = (
        Index("ix_resume_sections_resume_id", "resume_id"),
        Index("ix_resume_sections_resume_id_order", "resume_id", "sort_order"),
    )
