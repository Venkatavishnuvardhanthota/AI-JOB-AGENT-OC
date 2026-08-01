from __future__ import annotations

from typing import Any

import structlog

from app.ai.dependencies import get_ai_service

logger = structlog.get_logger(__name__)


async def ai_company_research(
    company: str,
    industry: str = "",
    role: str = "",
    company_url: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="company-research-ai",
        variables={
            "company": company,
            "industry": industry,
            "role": role,
            "company_url": company_url,
        },
        max_tokens=2500,
    )
    return {"research": result.content, "provider": result.provider, "model": result.model}


async def ai_job_summary(
    title: str,
    company: str,
    description: str = "",
    requirements: str = "",
    preferred_qualifications: str = "",
    profile_summary: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="job-summary-ai",
        variables={
            "title": title,
            "company": company,
            "description": description,
            "requirements": requirements,
            "preferred_qualifications": preferred_qualifications,
            "profile_summary": profile_summary,
        },
        max_tokens=2500,
    )
    return {"summary": result.content, "provider": result.provider, "model": result.model}
