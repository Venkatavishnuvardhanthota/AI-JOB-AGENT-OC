from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig
from app.intelligence.exceptions import LearningError

logger = structlog.get_logger(__name__)


class LearningEngine:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._events: list[dict[str, Any]] = []
        self._logger = logger.bind(engine="learning")

    async def learned_patterns(self) -> dict[str, Any]:
        if not self._events:
            return {"patterns": [], "total_events": 0}

        successful = [e for e in self._events if e.get("data", {}).get("outcome") == "success"]
        failed = [e for e in self._events if e.get("data", {}).get("outcome") == "failure"]

        patterns = {
            "total_events": len(self._events),
            "successful_events": len(successful),
            "failed_events": len(failed),
            "success_rate": round(len(successful) / len(self._events), 4) if self._events else 0.0,
            "recent_patterns": self._events[-10:] if len(self._events) > 10 else self._events,
        }
        return patterns

    async def learn(self, event_type: str, data: dict[str, Any]) -> None:
        if not self._config.learning_enabled:
            raise LearningError("Learning is disabled")

        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(event)
        self._logger.info("Learning event recorded", event_type=event_type, data_keys=list(data.keys()))

    async def record_successful_application(self, data: dict[str, Any]) -> None:
        data["outcome"] = "success"
        await self.learn("successful_application", data)

    async def record_failed_application(self, data: dict[str, Any]) -> None:
        data["outcome"] = "failure"
        await self.learn("failed_application", data)

    async def record_manual_intervention(self, data: dict[str, Any]) -> None:
        await self.learn("manual_intervention", data)

    async def record_resume_performance(self, data: dict[str, Any]) -> None:
        await self.learn("resume_performance", data)

    async def record_ai_output(self, data: dict[str, Any]) -> None:
        await self.learn("ai_output", data)

    async def record_provider_reliability(self, data: dict[str, Any]) -> None:
        await self.learn("provider_reliability", data)

    async def record_matching_quality(self, data: dict[str, Any]) -> None:
        await self.learn("matching_quality", data)

    async def record_workflow_history(self, data: dict[str, Any]) -> None:
        await self.learn("workflow_history", data)

    @property
    def events(self) -> list[dict[str, Any]]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
