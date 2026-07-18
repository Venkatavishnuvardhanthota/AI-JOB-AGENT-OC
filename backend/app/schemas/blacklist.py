import uuid
from datetime import datetime

from pydantic import BaseModel


class BlacklistedCompanyBase(BaseModel):
    company_name: str
    reason: str | None = None


class BlacklistedCompanyCreate(BlacklistedCompanyBase):
    pass


class BlacklistedCompanyResponse(BlacklistedCompanyBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
