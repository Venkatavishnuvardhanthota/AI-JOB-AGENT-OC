import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base


class InterviewPrep(Base):
    __tablename__ = "interview_preps"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True
    )
    job_title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    behavioral_questions: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    technical_questions: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    salary_expectation: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    notice_period: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    strengths: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    weaknesses: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    career_goals: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    company_specific_answers: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", backref="interview_preps")
    job_posting = relationship("JobPosting", backref="interview_preps")
