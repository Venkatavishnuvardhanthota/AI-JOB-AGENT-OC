import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.company_research import (
    CompanyResearchRequest,
    CompanyResearchResponse,
    CompanyResearchSummary,
)
from app.services.company_research import CompanyResearchService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_research_service(
    db: AsyncSession = Depends(get_db),
) -> CompanyResearchService:
    return CompanyResearchService(session=db)


@router.post("/research", response_model=CompanyResearchResponse, status_code=201)
async def research_company(
    request: CompanyResearchRequest,
    current_user: User = Depends(get_current_user),
    service: CompanyResearchService = Depends(get_research_service),
) -> CompanyResearchResponse:
    result = await service.research(request.company_name)
    return CompanyResearchResponse(
        id=result.get("id", "00000000-0000-0000-0000-000000000000"),
        company_name=result["company_name"],
        industry=result.get("industry"),
        mission=result.get("mission"),
        values=result.get("values") or [],
        products_or_services=result.get("products_or_services") or [],
        company_culture=result.get("company_culture"),
        recent_news=result.get("recent_news") or [],
        headquarters=result.get("headquarters"),
        company_size=result.get("company_size"),
        linkedin_url=result.get("linkedin_url"),
        hiring_trends=result.get("hiring_trends") or [],
        technology_stack=result.get("technology_stack") or [],
        funding=result.get("funding"),
        summary=result.get("summary"),
        cached_at=result.get("cached_at"),
    )


@router.get("/research/{company_name}", response_model=CompanyResearchResponse)
async def get_company_research(
    company_name: str,
    current_user: User = Depends(get_current_user),
    service: CompanyResearchService = Depends(get_research_service),
) -> CompanyResearchResponse:
    result = await service.get_cached(company_name)
    if result is None:
        result = await service.research(company_name)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Company research not found."
        )
    return CompanyResearchResponse(
        id=result.get("id", "00000000-0000-0000-0000-000000000000"),
        company_name=result["company_name"],
        industry=result.get("industry"),
        mission=result.get("mission"),
        values=result.get("values") or [],
        products_or_services=result.get("products_or_services") or [],
        company_culture=result.get("company_culture"),
        recent_news=result.get("recent_news") or [],
        headquarters=result.get("headquarters"),
        company_size=result.get("company_size"),
        linkedin_url=result.get("linkedin_url"),
        hiring_trends=result.get("hiring_trends") or [],
        technology_stack=result.get("technology_stack") or [],
        funding=result.get("funding"),
        summary=result.get("summary"),
        cached_at=result.get("cached_at"),
    )


@router.get(
    "/research/{company_name}/summary",
    response_model=CompanyResearchSummary,
)
async def get_company_research_summary(
    company_name: str,
    current_user: User = Depends(get_current_user),
    service: CompanyResearchService = Depends(get_research_service),
) -> CompanyResearchSummary:
    summary = await service.get_summary(company_name)
    return CompanyResearchSummary(
        company_name=company_name,
        summary=summary,
    )


@router.delete("/research/{company_name}", status_code=204)
async def invalidate_company_research(
    company_name: str,
    current_user: User = Depends(get_current_user),
    service: CompanyResearchService = Depends(get_research_service),
) -> None:
    await service.invalidate_cache(company_name)
