import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    name: str
    category: str | None = None
    proficiency: int | None = Field(None, ge=1, le=5)


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    proficiency: int | None = Field(None, ge=1, le=5)


class SkillResponse(SkillBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
