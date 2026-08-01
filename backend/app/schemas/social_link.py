import uuid
from datetime import datetime

from pydantic import BaseModel, Field, computed_field, field_validator

from app.schemas.validators import validate_url

SOCIAL_LINK_PLATFORMS = ["linkedin", "github", "portfolio", "website", "other"]

SOCIAL_LINK_TITLES = {
    "linkedin": "LinkedIn",
    "github": "GitHub",
    "portfolio": "Portfolio",
    "website": "Personal Website",
    "other": "Other",
}


def normalize_platform(value: str) -> str:
    platform = value.strip().lower().replace(" ", "")
    if platform not in SOCIAL_LINK_PLATFORMS:
        raise ValueError(
            f"Platform must be one of: {', '.join(SOCIAL_LINK_PLATFORMS)}"
        )
    return platform


def coerce_platform(value: str) -> str:
    platform = value.strip().lower().replace(" ", "")
    return platform if platform in SOCIAL_LINK_PLATFORMS else "other"


class SocialLinkBase(BaseModel):
    platform: str = Field(max_length=50)
    url: str = Field(min_length=1, max_length=2048)
    display_order: int | None = None

    @field_validator("platform")
    @classmethod
    def _validate_platform(cls, v: str) -> str:
        return normalize_platform(v)

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        validated = validate_url(v)
        if validated is None:
            raise ValueError("URL is required")
        return validated


class SocialLinkCreate(SocialLinkBase):
    pass


class SocialLinkUpdate(BaseModel):
    platform: str | None = Field(None, max_length=50)
    url: str | None = Field(None, min_length=1, max_length=2048)
    display_order: int | None = None

    @field_validator("platform")
    @classmethod
    def _validate_platform(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return normalize_platform(v)

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        return validate_url(v)


class SocialLinkResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    platform: str
    url: str
    display_order: int | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("platform")
    @classmethod
    def _coerce_platform(cls, v: str) -> str:
        return coerce_platform(v)

    @computed_field
    @property
    def title(self) -> str:
        return SOCIAL_LINK_TITLES[self.platform]

    class Config:
        from_attributes = True
