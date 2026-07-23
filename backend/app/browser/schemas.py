from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BrowserType(str, Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserState(str, Enum):
    CLOSED = "closed"
    LAUNCHING = "launching"
    OPEN = "open"
    ERROR = "error"


class ContextState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class SessionState(str, Enum):
    CREATED = "created"
    NAVIGATING = "navigating"
    ACTIVE = "active"
    CLOSED = "closed"
    ERROR = "error"


class ViewportSize(BaseModel):
    width: int = 1920
    height: int = 1080


class Cookie(BaseModel):
    name: str
    value: str
    domain: str | None = None
    path: str | None = None
    expires: float | None = None
    http_only: bool = False
    secure: bool = False
    same_site: str | None = None


class BrowserInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    browser_type: BrowserType = BrowserType.CHROMIUM
    state: BrowserState = BrowserState.CLOSED
    headless: bool = True
    launched_at: datetime | None = None
    context_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    browser_id: str
    state: ContextState = ContextState.OPEN
    is_persistent: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    page_count: int = 0
    storage_state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    browser_id: str
    context_id: str
    state: SessionState = SessionState.CREATED
    current_url: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NavigationResult(BaseModel):
    success: bool = True
    url: str
    status_code: int | None = None
    title: str | None = None
    duration_ms: float = 0.0
    error: str | None = None


class ScreenshotOptions(BaseModel):
    full_page: bool = False
    quality: int | None = None
    type: str = "png"
    timeout_ms: float | None = None


class UploadFile(BaseModel):
    file_path: str
    file_name: str
    file_size_bytes: int = 0
    mime_type: str = "application/octet-stream"
    selector: str | None = None


class DownloadInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str | None = None
    suggested_filename: str | None = None
    file_path: str | None = None
    file_size_bytes: int = 0
    success: bool = False
    error: str | None = None
    downloaded_at: datetime = Field(default_factory=datetime.utcnow)
