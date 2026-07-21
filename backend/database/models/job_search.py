import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class JobSearch(Base):
    __tablename__ = "job_searches"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    filters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    results_count: Mapped[int | None] = mapped_column(nullable=True)

    user = relationship("User", back_populates="job_searches")

    __table_args__ = (Index("ix_job_searches_user_id", "user_id"),)
