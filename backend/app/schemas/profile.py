import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserProfileBase(BaseModel):
    phone: str | None = None
    headline: str | None = None
    bio: str | None = None
    location: str | None = None
    salary_expectation_min: int | None = None
    salary_expectation_max: int | None = None
    salary_currency: str | None = Field(None, max_length=3)
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_file: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
