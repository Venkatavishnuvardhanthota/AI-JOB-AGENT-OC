from __future__ import annotations

from typing import Any

import structlog

from app.ai.dependencies import get_ai_service

logger = structlog.get_logger(__name__)


async def ai_generate_email(
    email_type: str,
    recipient: str = "",
    recipient_title: str = "",
    company: str = "",
    your_name: str = "",
    job_title: str = "",
    context: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="email-generation",
        variables={
            "email_type": email_type,
            "recipient": recipient,
            "recipient_title": recipient_title,
            "company": company,
            "your_name": your_name,
            "job_title": job_title,
            "context": context,
        },
        max_tokens=1500,
    )
    return {"email": result.content, "provider": result.provider, "model": result.model}
