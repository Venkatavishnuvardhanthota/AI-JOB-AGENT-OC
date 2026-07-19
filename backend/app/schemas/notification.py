import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str
    is_read: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationListItem(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    is_read: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class MarkReadRequest(BaseModel):
    notification_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)


class UnreadCountResponse(BaseModel):
    count: int
