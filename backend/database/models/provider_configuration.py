from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class ProviderConfiguration(Base):
    __tablename__ = "provider_configurations"

    provider_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_provider_configurations_provider_type", "provider_type"),
        Index("ix_provider_configurations_is_enabled", "is_enabled"),
    )
