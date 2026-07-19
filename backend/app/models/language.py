from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid as Uuid

from app.models.base import Base


class Language(Base):
    __tablename__ = "languages"

    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_language_name"),
    )

    def __repr__(self) -> str:
        return f"<Language(id={self.id}, name={self.name})>"
