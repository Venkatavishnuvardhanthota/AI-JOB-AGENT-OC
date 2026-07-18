import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PortfolioItemBase(BaseModel):
    title: str
    description: str | None = None
    url: str | None = None
    media_url: str | None = None
    technologies: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class PortfolioItemCreate(PortfolioItemBase):
    pass


class PortfolioItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    url: str | None = None
    media_url: str | None = None
    technologies: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class PortfolioItemResponse(PortfolioItemBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
