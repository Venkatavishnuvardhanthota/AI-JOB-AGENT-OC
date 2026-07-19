from datetime import datetime

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str = Field(..., pattern=r"^(system|user|assistant|tool)$")
    content: str


class LLMRequest(BaseModel):
    messages: list[LLMMessage]
    model: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128_000)
    stop: list[str] | None = None
    stream: bool = False


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: dict | None = None
    latency_ms: float | None = None


class EmbeddingRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=100)
    model: str | None = None


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    provider: str
    dimension: int


class VectorDocument(BaseModel):
    id: str
    content: str
    metadata: dict | None = None
    score: float | None = None


class VectorSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


class VectorSearchResponse(BaseModel):
    results: list[VectorDocument]


class RAGRequest(BaseModel):
    query: str
    system_prompt: str | None = None
    top_k: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.3, ge=0.0, le=1.0)
    model: str | None = None
    temperature: float | None = None


class RAGResponse(BaseModel):
    answer: str
    sources: list[VectorDocument]
    model: str
    provider: str
    usage: dict | None = None


class PromptTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    template: str = Field(..., min_length=1)
    variables: list[str] = []
    description: str | None = None
    model: str | None = None


class PromptTemplateUpdate(BaseModel):
    template: str | None = None
    variables: list[str] | None = None
    description: str | None = None
    model: str | None = None
    is_active: bool | None = None


class PromptTemplateResponse(BaseModel):
    id: str
    name: str
    version: int
    template: str
    variables: list[str]
    description: str | None
    model: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptRenderRequest(BaseModel):
    name: str
    version: int | None = None
    variables: dict[str, str] = {}


class PromptRenderResponse(BaseModel):
    rendered: str
    name: str
    version: int


class LLMProviderConfig(BaseModel):
    provider: str = Field(..., pattern=r"^(openai|anthropic|gemini|ollama|openrouter)$")
    api_key: str | None = None
    base_url: str | None = None
    default_model: str = "gpt-4o"
    timeout: int = 60
    max_retries: int = 3
