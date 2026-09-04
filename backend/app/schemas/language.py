import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.validators import title_case


class LanguageBase(BaseModel):
    language: str = Field(min_length=1, max_length=100)
    proficiency: str | None = Field(None, max_length=100)

    @field_validator("language")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        return v.strip().title() or v


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(BaseModel):
    language: str | None = Field(None, min_length=1, max_length=100)
    proficiency: str | None = Field(None, max_length=100)

    @field_validator("language", "proficiency")
    @classmethod
    def _clean(cls, v: str | None) -> str | None:
        cleaned = title_case(v)
        if v is not None and cleaned is None:
            raise ValueError("Value cannot be empty")
        return cleaned


class LanguageResponse(LanguageBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
