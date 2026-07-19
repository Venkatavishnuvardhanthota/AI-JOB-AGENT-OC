import json
import logging

from app.schemas.llm import LLMMessage, LLMRequest
from app.services.llm.factory import get_llm_client

logger = logging.getLogger(__name__)


class TruthValidator:
    async def validate(self, statements: list[str], context: str | None = None) -> list[dict]:
        if not statements:
            return []

        client = get_llm_client()
        if not client:
            logger.warning("No LLM client available for truth validation")
            return self._fallback_results(statements)

        system_prompt = (
            "You are a truth validation assistant. Given a list of statements "
            "and optional context, analyze each statement for consistency and "
            "plausibility. Return a JSON array of objects with these fields:\n"
            "- statement (string, the original statement)\n"
            "- is_consistent (boolean, whether the statement appears truthful)\n"
            "- confidence (float 0.0-1.0, how confident you are)\n"
            "- inconsistencies (list of strings describing any issues found)\n"
            "- suggestions (list of strings suggesting improvements)\n"
            "Be fair and constructive. Flag unrealistic claims gently."
        )
        user_prompt = f"Context: {context or 'No additional context provided.'}\n\nStatements:\n"
        for i, stmt in enumerate(statements, 1):
            user_prompt += f"{i}. {stmt}\n"

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.2,
            max_tokens=2000,
        )

        try:
            response = await client.complete(request)
            parsed = json.loads(response.content)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "results" in parsed:
                return parsed["results"]
            logger.warning("Unexpected response format from truth validator")
            return self._fallback_results(statements)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse truth validation response: %s", e)
            return self._fallback_results(statements)
        except Exception as e:
            logger.error("Truth validation failed: %s", str(e))
            return self._fallback_results(statements)

    @staticmethod
    def _fallback_results(statements: list[str]) -> list[dict]:
        return [
            {
                "statement": stmt,
                "is_consistent": True,
                "confidence": 0.0,
                "inconsistencies": [],
                "suggestions": ["Could not validate automatically."],
            }
            for stmt in statements
        ]
