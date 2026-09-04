from __future__ import annotations

import re

import structlog

from app.ai.exceptions import MissingVariableError, RenderError
from app.ai.prompts.template import PromptTemplate

logger = structlog.get_logger(__name__)

# Characters/patterns that suggest prompt injection attempts
_INJECTION_PATTERNS = re.compile(
    r"(?i)(ignore\s+(all\s+)?(previous|above|prior)\s+instructions"
    r"|forget\s+(all\s+)?(previous|above|prior)"
    r"|new\s+instructions?"
    r"|override\s+(all\s+)?(previous|above|prior)"
    r"|system\s+prompt"
    r"|reveal\s+(your|the)\s+(system\s+)?prompt"
    r"|output\s+(your|the)\s+(system\s+)?prompt"
    r"|print\s+(your|the)\s+(system\s+)?prompt"
    r"|you\s+are\s+(now\s+)?(an?\s+)?(assistant|ai|model|bot|agent)"
    r"|act\s+as(\s+an?\s+)?"
    r"|from\s+now\s+on"
    r"|<\|(system|assistant|user|developer)\|>"
    r"|#{1,6}\s*(system|assistant|user|developer|instructions|prompt)\b"
    r"|^\s*(system|assistant|user|developer)\s*:"
    r")",
    re.MULTILINE,
)

# Maximum length for any single user variable value to prevent token flooding
_MAX_VARIABLE_LENGTH = 50000


class PromptRenderer:
    def render(self, template: PromptTemplate, variables: dict[str, str]) -> str:
        required = template.variables
        missing = [v for v in required if v not in variables]
        if missing:
            raise MissingVariableError(f"Missing required template variables: {', '.join(missing)}")

        sanitized = {}
        for key, value in variables.items():
            if not isinstance(value, str):
                sanitized[key] = str(value)
                continue
            truncated = value[:_MAX_VARIABLE_LENGTH]
            if _INJECTION_PATTERNS.search(truncated):
                logger.warning("Prompt injection pattern detected", variable=key)
                raise RenderError(f"Prompt injection detected in variable '{key}'.")
            sanitized[key] = truncated

        try:
            result = template.template.format(**sanitized)
        except KeyError as exc:
            raise RenderError(f"Missing variable in template: {exc}") from exc
        except ValueError as exc:
            raise RenderError(f"Template formatting error: {exc}") from exc

        unresolved = re.findall(r"\{(\w+)\}", result)
        if unresolved:
            raise RenderError(f"Template contains unresolved placeholders: {', '.join(unresolved)}")

        return result
