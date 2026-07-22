from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost: float | None = Field(default=None, ge=0.0)


class GenerationMetadata(BaseModel):
    model: str
    provider: str
    finish_reason: str | None = None
    duration_ms: int | None = None
    id: str | None = None


class AIRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=100000)
    system_prompt: str | None = Field(default=None, max_length=10000)
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=100000)
    provider: str | None = None
    stop_sequences: list[str] | None = None


class AIResponse(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    content: str
    model: str
    provider: str
    usage: UsageMetrics = Field(default_factory=UsageMetrics)
    metadata: GenerationMetadata | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: str | None = None
    max_tokens: int | None = None
    supports_streaming: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False


class ProviderInfo(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    models: list[ModelInfo] = Field(default_factory=list)
    is_available: bool = False
    version: str | None = None
    supports_streaming: bool = False
