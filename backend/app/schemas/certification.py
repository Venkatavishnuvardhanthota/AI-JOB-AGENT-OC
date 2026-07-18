import uuid
from datetime import date, datetime

from pydantic import BaseModel


class CertificationBase(BaseModel):
    name: str
    issuer: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: str | None = None
    issuer: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    credential_url: str | None = None


class CertificationResponse(CertificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    file_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
