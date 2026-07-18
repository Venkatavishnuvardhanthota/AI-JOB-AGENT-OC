import uuid
from datetime import datetime

from pydantic import BaseModel


class LanguageBase(BaseModel):
    name: str
    proficiency: str


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(BaseModel):
    name: str | None = None
    proficiency: str | None = None


class LanguageResponse(LanguageBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
