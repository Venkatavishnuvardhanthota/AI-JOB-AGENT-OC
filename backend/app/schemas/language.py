import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LanguageBase(BaseModel):
    language: str = Field(max_length=100)
    proficiency: str | None = Field(None, max_length=100)


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(BaseModel):
    language: str | None = Field(None, max_length=100)
    proficiency: str | None = Field(None, max_length=100)


class LanguageResponse(LanguageBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
