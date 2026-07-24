from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig

logger = structlog.get_logger(__name__)


class IntelligenceHistory:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._entries: list[dict[str, Any]] = []
        self._logger = logger.bind(engine="history")

    async def record(self, event_type: str, description: str, data: dict[str, Any]) -> None:
        entry = {
            "event_type": event_type,
            "description": description,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._entries.append(entry)
        self._trim()
        self._logger.info("History entry recorded", event_type=event_type)

    def _trim(self) -> None:
        if len(self._entries) > self._config.history_max_entries:
            excess = len(self._entries) - self._config.history_max_entries
            self._entries = self._entries[excess:]

        cutoff = datetime.now(timezone.utc) - timedelta(days=self._config.history_retention_days)
        self._entries = [
            e for e in self._entries if datetime.fromisoformat(e["timestamp"]).replace(tzinfo=timezone.utc) > cutoff
        ]

    async def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._entries)[-limit:]

    async def get_by_type(self, event_type: str, limit: int = 100) -> list[dict[str, Any]]:
        filtered = [e for e in self._entries if e["event_type"] == event_type]
        return filtered[-limit:]

    async def get_recent(self, minutes: int = 60) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [
            e for e in self._entries if datetime.fromisoformat(e["timestamp"]).replace(tzinfo=timezone.utc) > cutoff
        ]

    async def get_statistics(self) -> dict[str, Any]:
        if not self._entries:
            return {"total": 0, "by_type": {}}

        by_type: dict[str, int] = {}
        for entry in self._entries:
            by_type[entry["event_type"]] = by_type.get(entry["event_type"], 0) + 1

        return {
            "total": len(self._entries),
            "by_type": by_type,
            "oldest": self._entries[0]["timestamp"] if self._entries else None,
            "newest": self._entries[-1]["timestamp"] if self._entries else None,
        }

    async def clear(self) -> None:
        self._entries.clear()
        self._logger.info("History cleared")

    @property
    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)
