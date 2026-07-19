from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid as Uuid

from app.models.base import Base


class Certification(Base):
    __tablename__ = "certifications"

    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credential_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    credential_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    file_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_certification_name"),
    )

    def __repr__(self) -> str:
        return f"<Certification(id={self.id}, name={self.name})>"
