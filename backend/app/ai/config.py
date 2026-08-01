from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    default_provider: str = Field(default="openrouter", description="Default AI provider name")
    default_model: str = Field(default="gpt-4o", description="Default model identifier")
    fallback_model: str = Field(default="gpt-3.5-turbo", description="Fallback model if primary unavailable")
    fallback_provider: str | None = Field(default=None, description="Fallback AI provider if primary fails")
    max_retries: int = Field(default=3, ge=0, description="Number of retry attempts on transient failure")
    retry_delay_seconds: int = Field(default=1, ge=0, description="Base delay between retries in seconds")
    timeout_seconds: int = Field(default=60, ge=1, description="Provider request timeout in seconds")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Default generation temperature")
    max_tokens: int | None = Field(default=None, ge=1, description="Default max tokens per generation")
    enabled_providers: list[str] = Field(
        default_factory=lambda: ["openrouter"], description="List of enabled providers"
    )
    streaming_enabled: bool = Field(default=False, description="Enable streaming responses")

    # OpenRouter
    openrouter_api_key: str | None = Field(default=None, description="OpenRouter API key")
    openrouter_base_url: str = Field(default="https://openrouter.ai", description="OpenRouter API base URL")
    openrouter_default_model: str = Field(default="gpt-4o", description="OpenRouter default model")

    # OpenAI
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_base_url: str = Field(default="https://api.openai.com", description="OpenAI API base URL")
    openai_default_model: str = Field(default="gpt-4o", description="OpenAI default model")

    # Anthropic
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_base_url: str = Field(default="https://api.anthropic.com", description="Anthropic API base URL")
    anthropic_default_model: str = Field(default="claude-sonnet-4-20250514", description="Anthropic default model")

    # Gemini
    gemini_api_key: str | None = Field(default=None, description="Gemini API key")
    gemini_base_url: str = Field(default="https://generativelanguage.googleapis.com", description="Gemini API base URL")
    gemini_default_model: str = Field(default="gemini-2.0-flash", description="Gemini default model")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama server base URL")
    ollama_default_model: str = Field(default="llama3", description="Ollama default model")
