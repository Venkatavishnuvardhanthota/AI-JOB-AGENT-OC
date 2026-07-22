from __future__ import annotations

import re

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    name: str = Field(min_length=1, description="Unique template name")
    template: str = Field(min_length=1, description="Prompt template with {variable} placeholders")
    system_prompt: str | None = Field(default=None, description="Optional system-level instructions")
    description: str | None = Field(default=None, description="Human-readable description")
    version: str = Field(default="1.0.0", description="Template version")

    @property
    def variables(self) -> list[str]:
        return re.findall(r"\{(\w+)\}", self.template)
