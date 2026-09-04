from __future__ import annotations

from typing import Any

import structlog

from app.ai.dependencies import get_ai_service

logger = structlog.get_logger(__name__)


async def ai_enhance_matching(
    job_title: str,
    company: str,
    job_description: str = "",
    profile_skills: str = "",
    profile_experience: str = "",
    profile_education: str = "",
    current_score: float = 0.0,
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="matching-analysis-ai",
        variables={
            "job_title": job_title,
            "company": company,
            "job_description": job_description[:3000],
            "profile_skills": profile_skills,
            "profile_experience": profile_experience,
            "profile_education": profile_education,
            "current_score": str(current_score),
        },
        max_tokens=2000,
    )
    return {"analysis": result.content, "provider": result.provider, "model": result.model}
