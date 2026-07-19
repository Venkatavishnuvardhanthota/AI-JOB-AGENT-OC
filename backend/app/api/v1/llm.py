from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.llm import (
    EmbeddingRequest,
    EmbeddingResponse,
    LLMRequest,
    LLMResponse,
    PromptRenderRequest,
    PromptRenderResponse,
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateUpdate,
    RAGRequest,
    RAGResponse,
    VectorSearchRequest,
    VectorSearchResponse,
)
from app.services.llm.config import llm_config
from app.services.llm.embeddings import EmbeddingService
from app.services.llm.factory import get_llm_client, list_providers
from app.services.llm.prompts.registry import PromptRegistry
from app.services.llm.prompts.templates import PromptTemplateService
from app.services.llm.rag import RAGService
from app.services.llm.vector_store import VectorStore

router = APIRouter()

_vector_store = VectorStore()
_prompt_registry = PromptRegistry()


@router.get("/providers")
async def get_providers():
    """List available LLM providers."""
    providers = list_providers()
    return {
        "providers": providers,
        "default": llm_config.default_provider,
        "embedding_provider": llm_config.embedding_provider,
        "embedding_model": llm_config.embedding_model,
    }


@router.post("/chat", response_model=LLMResponse)
async def llm_chat(
    request: LLMRequest,
    provider: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Send a chat completion request to an LLM provider."""
    client = get_llm_client(provider)
    if not client:
        provider_name = provider or llm_config.default_provider
        raise HTTPException(
            status_code=400,
            detail=f"LLM provider '{provider_name}' not available",
        )
    return await client.complete(request)


@router.post("/embed", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate embeddings for input texts."""
    svc = EmbeddingService()
    return await svc.embed(request.texts)


@router.post("/vector/add")
async def vector_add_document(
    doc_id: str,
    content: str,
    metadata: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Add a document with its embedding to the vector store."""
    svc = EmbeddingService()
    emb_resp = await svc.embed([content])
    import json
    _vector_store.add_document(
        doc_id=doc_id,
        content=content,
        embedding=emb_resp.embeddings[0],
        metadata=json.loads(metadata) if metadata else None,
    )
    return {"status": "added", "doc_id": doc_id}


@router.post("/vector/search", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Search the vector store for similar documents."""
    svc = EmbeddingService()
    emb_resp = await svc.embed([request.query])
    results = _vector_store.search(
        query_embedding=emb_resp.embeddings[0],
        top_k=request.top_k,
        min_score=request.min_score,
    )
    return VectorSearchResponse(results=results)


@router.post("/rag/query", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    current_user: User = Depends(get_current_user),
):
    """Query documents using Retrieval Augmented Generation."""
    svc = EmbeddingService()
    rag = RAGService(vector_store=_vector_store, embedding_service=svc)
    return await rag.query(request)


@router.get("/prompts/registry")
async def list_registry_prompts(
    current_user: User = Depends(get_current_user),
):
    """List built-in prompt templates from the registry."""
    return _prompt_registry.list_prompts()


@router.get("/prompts/registry/{name}")
async def get_registry_prompt(
    name: str,
    version: int | None = None,
    current_user: User = Depends(get_current_user),
):
    """Get a specific prompt from the registry."""
    prompt = _prompt_registry.get_prompt(name, version)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/prompts/registry/render")
async def render_registry_prompt(
    request: PromptRenderRequest,
    current_user: User = Depends(get_current_user),
):
    """Render a registry prompt with variables."""
    result = _prompt_registry.render(request.name, request.variables, request.version)
    if not result:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result


@router.post("/prompts/templates", response_model=PromptTemplateResponse)
async def create_prompt_template(
    data: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new prompt template."""
    svc = PromptTemplateService(db)
    return await svc.create(data)


@router.get("/prompts/templates", response_model=list[PromptTemplateResponse])
async def list_prompt_templates(
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List stored prompt templates."""
    svc = PromptTemplateService(db)
    return await svc.list_templates(name)


@router.get("/prompts/templates/{name}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    name: str,
    version: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific prompt template version."""
    svc = PromptTemplateService(db)
    pt = await svc.get(name, version)
    if not pt:
        raise HTTPException(status_code=404, detail="Template not found")
    return pt


@router.put("/prompts/templates/{name}/version/{version}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    name: str,
    version: int,
    data: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a specific prompt template version."""
    svc = PromptTemplateService(db)
    pt = await svc.update(name, version, data)
    if not pt:
        raise HTTPException(status_code=404, detail="Template not found")
    return pt


@router.post("/prompts/templates/{name}/versions", response_model=PromptTemplateResponse)
async def create_prompt_version(
    name: str,
    data: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new version of a prompt template."""
    svc = PromptTemplateService(db)
    pt = await svc.create_new_version(name, data)
    if not pt:
        raise HTTPException(status_code=404, detail="Failed to create version")
    return pt


@router.post("/prompts/templates/render", response_model=PromptRenderResponse)
async def render_prompt_template(
    request: PromptRenderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Render a stored prompt template with variables."""
    svc = PromptTemplateService(db)
    rendered = await svc.render(request.name, request.variables, request.version)
    if rendered is None:
        raise HTTPException(status_code=404, detail="Template not found")
    pt = await svc.get(request.name, request.version)
    return PromptRenderResponse(rendered=rendered, name=request.name, version=pt.version if pt else 0)
