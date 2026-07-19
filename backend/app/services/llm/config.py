from pydantic import BaseModel


class LLMProviderItem(BaseModel):
    provider: str
    api_key: str | None = None
    base_url: str | None = None
    default_model: str
    timeout: int = 60
    max_retries: int = 3
    enabled: bool = True


class LLMConfig(BaseModel):
    providers: dict[str, LLMProviderItem] = {
        "openai": LLMProviderItem(
            provider="openai",
            default_model="gpt-4o",
        ),
        "anthropic": LLMProviderItem(
            provider="anthropic",
            default_model="claude-3-5-sonnet-latest",
        ),
        "gemini": LLMProviderItem(
            provider="gemini",
            default_model="gemini-2.0-flash",
        ),
        "ollama": LLMProviderItem(
            provider="ollama",
            default_model="llama3.2",
            base_url="http://localhost:11434",
        ),
        "openrouter": LLMProviderItem(
            provider="openrouter",
            default_model="openai/gpt-4o",
        ),
    }
    default_provider: str = "openai"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000
    vector_store_top_k: int = 10
    vector_store_min_score: float = 0.3
    max_tokens_default: int = 4096
    temperature_default: float = 0.7


llm_config = LLMConfig()
