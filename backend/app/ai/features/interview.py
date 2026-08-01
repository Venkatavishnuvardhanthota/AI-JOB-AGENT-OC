from __future__ import annotations

from typing import Any

import structlog

from app.ai.dependencies import get_ai_service

logger = structlog.get_logger(__name__)


async def ai_generate_interview_questions(
    job_title: str,
    company: str,
    job_description: str = "",
    background: str = "",
    question_types: str = "behavioral, technical, culture",
    interview_round: str = "first",
    count: int = 3,
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="interview-questions-ai",
        variables={
            "job_title": job_title,
            "company": company,
            "job_description": job_description,
            "background": background,
            "question_types": question_types,
            "interview_round": interview_round,
            "count": str(count),
        },
        max_tokens=3000,
    )
    return {"questions": result.content, "provider": result.provider, "model": result.model}


async def ai_answer_application_questions(
    job_title: str,
    company: str,
    job_description: str = "",
    profile_summary: str = "",
    questions: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="application-questions-ai",
        variables={
            "job_title": job_title,
            "company": company,
            "job_description": job_description,
            "profile_summary": profile_summary,
            "questions": questions,
        },
        max_tokens=2500,
    )
    return {"answers": result.content, "provider": result.provider, "model": result.model}
