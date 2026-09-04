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


class CapabilityInfo(BaseModel):
    chat: bool = True
    streaming: bool = False
    vision: bool = False
    json_mode: bool = False
    embeddings: bool = False
    reasoning: bool = False
    function_calling: bool = False
    tool_calling: bool = False
    system_prompt_support: bool = True
    structured_output: bool = False


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
    supports_json_mode: bool = False
    supports_reasoning: bool = False


class ProviderInfo(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    models: list[ModelInfo] = Field(default_factory=list)
    is_available: bool = False
    version: str | None = None
    supports_streaming: bool = False
    capabilities: CapabilityInfo = Field(default_factory=CapabilityInfo)
    configured: bool = False
    enabled: bool = True
    is_default: bool = False
    error: str | None = None


class ProviderStatus(BaseModel):
    name: str
    display_name: str
    configured: bool
    enabled: bool
    healthy: bool | None = None
    connected: bool | None = None
    is_default: bool
    available: bool
    implementation_status: str = "implemented"
    capabilities: CapabilityInfo = Field(default_factory=CapabilityInfo)
    models: list[ModelInfo] = Field(default_factory=list)
    error: str | None = None


class HealthCheckResult(BaseModel):
    provider: str
    model: str | None = None
    healthy: bool
    connected: bool | None = None
    latency_ms: float | None = None
    available: bool = False
    configured: bool = False
    is_default: bool = False
    error: str | None = None


class AIUpdateConfig(BaseModel):
    default_provider: str | None = None
    default_model: str | None = None
    fallback_provider: str | None = None
    fallback_model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: int | None = Field(default=None, ge=1)
    max_retries: int | None = Field(default=None, ge=0)
    retry_delay_seconds: int | None = Field(default=None, ge=0)
    streaming_enabled: bool | None = None
    enabled_providers: list[str] | None = None
    openrouter_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    ollama_base_url: str | None = None


class AIProviderConfigUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None
    is_enabled: bool | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: int | None = Field(default=None, ge=1)
    max_retries: int | None = Field(default=None, ge=0)
    retry_delay_seconds: int | None = Field(default=None, ge=0)
    streaming_enabled: bool | None = None
