import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class CertificationBase(BaseModel):
    name: str = Field(max_length=255)
    issuer: str | None = Field(None, max_length=255)
    credential_id: str | None = Field(None, max_length=255)
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_url: str | None = None


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    issuer: str | None = Field(None, max_length=255)
    credential_id: str | None = Field(None, max_length=255)
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_url: str | None = None


class CertificationResponse(CertificationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
