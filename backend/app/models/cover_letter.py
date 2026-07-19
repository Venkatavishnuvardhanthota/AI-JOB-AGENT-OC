import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    job_title: Mapped[str] = mapped_column(String(500), nullable=False)
    hiring_manager_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", backref="cover_letters")
    job_posting = relationship("JobPosting", backref="cover_letters")
