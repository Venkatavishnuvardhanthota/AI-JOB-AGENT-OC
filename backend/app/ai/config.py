from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    default_provider: str = Field(default="openrouter", description="Default AI provider name")
    default_model: str = Field(default="gpt-4o", description="Default model identifier")
    fallback_model: str = Field(default="gpt-3.5-turbo", description="Fallback model if primary unavailable")
    max_retries: int = Field(default=3, ge=0, description="Number of retry attempts on transient failure")
    timeout_seconds: int = Field(default=60, ge=1, description="Provider request timeout in seconds")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Default generation temperature")
    max_tokens: int | None = Field(default=None, ge=1, description="Default max tokens per generation")
    enabled_providers: list[str] = Field(
        default_factory=lambda: ["openrouter"], description="List of enabled providers"
    )
