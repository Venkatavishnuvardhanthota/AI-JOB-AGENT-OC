import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SkillBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    category: str | None = Field(None, max_length=100)
    proficiency: str | None = Field(None, max_length=50)
    years_experience: float | None = None
    skill_level: str | None = Field(None, max_length=50)
    display_order: int | None = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        return v.strip()


class SkillCreate(SkillBase):
    pass


class SkillBulkReplace(BaseModel):
    skills: list[str] = Field(min_length=1, max_length=200)

    @field_validator("skills")
    @classmethod
    def _clean_names(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in v:
            name = (item or "").strip()
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(name)
        if not cleaned:
            raise ValueError("At least one skill name is required.")
        return cleaned


class SkillUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    category: str | None = Field(None, max_length=100)
    proficiency: str | None = Field(None, max_length=50)
    years_experience: float | None = None
    skill_level: str | None = Field(None, max_length=50)
    display_order: int | None = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v


class SkillResponse(SkillBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
