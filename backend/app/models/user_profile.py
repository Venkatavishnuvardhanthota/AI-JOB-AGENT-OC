import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid as Uuid

from app.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_expectation_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    salary_expectation_max: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    salary_currency: Mapped[str | None] = mapped_column(
        String(3), nullable=True
    )
    portfolio_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    linkedin_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    github_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    resume_file: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="profile"
    )

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id})>"
