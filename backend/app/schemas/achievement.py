import uuid
from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import validate_url

ACHIEVEMENT_TYPES = [
    "Hackathon Winner",
    "Employee of the Month",
    "Kaggle Medal",
    "Research Publication",
    "Coding Contest",
    "Patent",
    "Award",
]


class AchievementBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    organization: str | None = Field(None, max_length=255)
    achievement_type: str | None = Field(None, max_length=100)
    date: date_type | None = None
    description: str | None = None
    url: str | None = None
    display_order: int | None = None

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        return validate_url(v)


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    organization: str | None = Field(None, max_length=255)
    achievement_type: str | None = Field(None, max_length=100)
    date: date_type | None = None
    description: str | None = None
    url: str | None = None
    display_order: int | None = None

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        return validate_url(v)


class AchievementResponse(AchievementBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
