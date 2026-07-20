import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)


class PaginatedResponse(BaseModel):
    data: list
    pagination: dict


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict | list | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: dict


class TimestampMixin(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
