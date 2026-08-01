import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class SocialLink(Base):
    __tablename__ = "social_links"

    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_profiles.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    profile = relationship("CareerProfile", back_populates="social_links")

    __table_args__ = (
        Index("ix_social_links_profile_id", "profile_id"),
        UniqueConstraint("profile_id", "platform", name="uq_social_link_profile_platform"),
        CheckConstraint(
            "platform IN ('linkedin', 'github', 'portfolio', 'website', 'other')",
            name="ck_social_link_platform",
        ),
    )
