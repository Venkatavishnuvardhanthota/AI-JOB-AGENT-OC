import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    name: str = Field(max_length=150)
    category: str | None = Field(None, max_length=100)
    proficiency: str | None = Field(None, max_length=50)
    years_experience: float | None = None
    skill_level: str | None = Field(None, max_length=50)
    display_order: int | None = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    category: str | None = Field(None, max_length=100)
    proficiency: str | None = Field(None, max_length=50)
    years_experience: float | None = None
    skill_level: str | None = Field(None, max_length=50)
    display_order: int | None = None


class SkillResponse(SkillBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
