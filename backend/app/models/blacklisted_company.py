from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid as Uuid

from app.models.base import Base


class BlacklistedCompany(Base):
    __tablename__ = "blacklisted_companies"

    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "company_name", name="uq_user_blacklisted_company"),
    )

    def __repr__(self) -> str:
        return f"<BlacklistedCompany(id={self.id}, company={self.company_name})>"
