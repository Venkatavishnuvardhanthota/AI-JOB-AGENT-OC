from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig

logger = structlog.get_logger(__name__)


class FeedbackProcessor:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._feedback: list[dict[str, Any]] = []
        self._logger = logger.bind(engine="feedback")

    async def record_feedback(self, category: str, data: dict[str, Any]) -> None:
        entry = {
            "category": category,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._feedback.append(entry)
        self._logger.info("Feedback recorded", category=category)

    async def get_feedback_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._feedback)[-limit:]

    async def get_feedback_by_category(self, category: str) -> list[dict[str, Any]]:
        return [f for f in self._feedback if f["category"] == category]

    async def get_feedback_summary(self) -> dict[str, Any]:
        if not self._feedback:
            return {"total": 0, "categories": {}}

        categories: dict[str, int] = {}
        for entry in self._feedback:
            cat = entry["category"]
            categories[cat] = categories.get(cat, 0) + 1

        ratings = [entry["data"].get("rating") for entry in self._feedback if entry["data"].get("rating") is not None]

        return {
            "total": len(self._feedback),
            "categories": categories,
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "total_ratings": len(ratings),
        }

    @property
    def feedback(self) -> list[dict[str, Any]]:
        return list(self._feedback)

    def clear(self) -> None:
        self._feedback.clear()
