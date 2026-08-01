import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.validators import validate_url


class CertificationBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    issuer: str | None = Field(None, max_length=255)
    credential_id: str | None = Field(None, max_length=255)
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_url: str | None = None

    @field_validator("credential_url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        return validate_url(v)

    @model_validator(mode="after")
    def _validate_dates(self):
        if (
            self.issue_date is not None
            and self.expiration_date is not None
            and self.expiration_date < self.issue_date
        ):
            raise ValueError("Expiration date must be on or after the issue date")
        return self


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    issuer: str | None = Field(None, max_length=255)
    credential_id: str | None = Field(None, max_length=255)
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_url: str | None = None

    @field_validator("credential_url")
    @classmethod
    def _validate_url(cls, v: str | None) -> str | None:
        return validate_url(v)

    @model_validator(mode="after")
    def _validate_dates(self):
        if (
            self.issue_date is not None
            and self.expiration_date is not None
            and self.expiration_date < self.issue_date
        ):
            raise ValueError("Expiration date must be on or after the issue date")
        return self


class CertificationResponse(CertificationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
