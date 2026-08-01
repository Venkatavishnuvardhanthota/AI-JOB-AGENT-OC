from __future__ import annotations

from typing import Any

import structlog

from app.ai.dependencies import get_ai_service

logger = structlog.get_logger(__name__)


async def ai_generate_cover_letter(
    job_title: str,
    company_name: str,
    job_description: str,
    resume_text: str,
    tone: str = "professional",
    style: str = "modern",
    hiring_manager: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="cover-letter-ai",
        variables={
            "style": style,
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
            "resume_text": resume_text,
            "tone": tone,
            "hiring_manager": hiring_manager,
        },
        max_tokens=1500,
    )
    return {"cover_letter": result.content, "provider": result.provider, "model": result.model}


async def ai_assist_cover_letter(
    content: str,
    instruction: str,
    context: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="cover-letter-ai-assist",
        variables={
            "instruction": instruction,
            "content": content,
            "context": context,
        },
        max_tokens=1500,
    )
    return {"edited_content": result.content, "provider": result.provider, "model": result.model}
