import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SocialLinkBase(BaseModel):
    platform: str = Field(max_length=50)
    url: str = Field(max_length=2048)
    display_order: int | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class SocialLinkCreate(SocialLinkBase):
    pass


class SocialLinkUpdate(BaseModel):
    platform: str | None = Field(None, max_length=50)
    url: str | None = Field(None, max_length=2048)
    display_order: int | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class SocialLinkResponse(SocialLinkBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
