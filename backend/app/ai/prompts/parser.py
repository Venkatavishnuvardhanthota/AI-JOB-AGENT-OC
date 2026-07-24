from __future__ import annotations

import json
import re
from typing import Any

import structlog
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.ai.exceptions import ResponseParsingError, ResponseValidationError

logger = structlog.get_logger(__name__)

JSON_FENCE_PATTERN = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)


class ResponseParser:
    def extract_json(self, content: str) -> Any:
        if not content or not content.strip():
            raise ResponseParsingError("Response content is empty.")

        match = JSON_FENCE_PATTERN.search(content)
        candidate = match.group(1).strip() if match else content.strip()

        candidate = re.sub(r"^[\s,]*", "", candidate)
        candidate = re.sub(r"[\s,]*$", "", candidate)

        if not candidate:
            raise ResponseParsingError("No JSON content found in response.")

        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            fixed = self._attempt_fix(candidate)
            if fixed is not None:
                return fixed
            raise ResponseParsingError(
                f"Failed to parse JSON response: {exc}. " f"Content preview: {candidate[:200]}"
            ) from exc

    def parse(self, content: str, response_model: type[BaseModel]) -> BaseModel:
        data = self.extract_json(content)
        try:
            return response_model.model_validate(data)
        except PydanticValidationError as exc:
            raise ResponseValidationError(f"Response validation failed: {exc}") from exc

    def _attempt_fix(self, text: str) -> Any | None:
        try:
            return json.loads(text.replace("'", '"'))
        except json.JSONDecodeError:
            pass

        try:
            return json.loads(text.strip().lstrip(",").rstrip(","))
        except json.JSONDecodeError:
            pass

        return None
