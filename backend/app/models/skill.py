from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid as Uuid

from app.models.base import Base


class Skill(Base):
    __tablename__ = "skills"

    user_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    proficiency: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name})>"
