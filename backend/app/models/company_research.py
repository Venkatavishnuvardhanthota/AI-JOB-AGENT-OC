from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class CompanyResearch(Base):
    __tablename__ = "company_research"

    company_name: Mapped[str] = mapped_column(
        String(500), unique=True, nullable=False, index=True
    )
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    values: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)
    products_or_services: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    company_culture: Mapped[str | None] = mapped_column(Text, nullable=True)
    recent_news: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)
    headquarters: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hiring_trends: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    technology_stack: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    funding: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    cached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
