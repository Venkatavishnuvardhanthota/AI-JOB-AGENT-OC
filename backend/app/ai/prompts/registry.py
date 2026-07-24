from __future__ import annotations

import structlog

from app.ai.exceptions import ConfigurationError, PromptTemplateError
from app.ai.prompts.template import PromptTemplate

logger = structlog.get_logger(__name__)


class PromptTemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        if not template.name:
            raise ConfigurationError("Prompt template must have a non-empty name.")
        if template.name in self._templates:
            logger.warning("Overwriting existing prompt template", name=template.name)
        self._templates[template.name] = template
        logger.info("Registered prompt template", name=template.name, variables=template.variables)

    def get(self, name: str) -> PromptTemplate:
        template = self._templates.get(name)
        if template is None:
            registered = list(self._templates.keys())
            raise PromptTemplateError(f"Prompt template '{name}' not found. Registered templates: {registered}")
        return template

    def list(self) -> list[PromptTemplate]:
        return list(self._templates.values())

    def list_names(self) -> list[str]:
        return list(self._templates.keys())

    def unregister(self, name: str) -> None:
        if name not in self._templates:
            raise PromptTemplateError(f"Prompt template '{name}' is not registered.")
        del self._templates[name]
        logger.info("Unregistered prompt template", name=name)

    def is_registered(self, name: str) -> bool:
        return name in self._templates

    def count(self) -> int:
        return len(self._templates)

    def clear(self) -> None:
        self._templates.clear()
