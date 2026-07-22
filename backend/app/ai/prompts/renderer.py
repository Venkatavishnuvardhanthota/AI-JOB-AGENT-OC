from __future__ import annotations

import re

import structlog

from app.ai.exceptions import MissingVariableError, RenderError
from app.ai.prompts.template import PromptTemplate

logger = structlog.get_logger(__name__)


class PromptRenderer:
    def render(self, template: PromptTemplate, variables: dict[str, str]) -> str:
        required = template.variables
        missing = [v for v in required if v not in variables]
        if missing:
            raise MissingVariableError(
                f"Missing required template variables: {', '.join(missing)}"
            )

        try:
            result = template.template.format(**variables)
        except KeyError as exc:
            raise RenderError(f"Missing variable in template: {exc}") from exc
        except ValueError as exc:
            raise RenderError(f"Template formatting error: {exc}") from exc

        unresolved = re.findall(r"\{(\w+)\}", result)
        if unresolved:
            raise RenderError(
                f"Template contains unresolved placeholders: {', '.join(unresolved)}"
            )

        return result
