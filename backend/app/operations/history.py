from __future__ import annotations

from datetime import datetime, timedelta
from threading import Lock
from typing import Any

from app.operations.config import OperationsConfig
from app.operations.exceptions import HistoryError
from app.operations.interfaces import ExecutionHistory
from app.operations.schemas import HistoryEntry


class OperationsExecutionHistory(ExecutionHistory):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config
        self._lock = Lock()
        self._entries: list[HistoryEntry] = []

    def record(self, entry: dict[str, Any]) -> None:
        try:
            history_entry = HistoryEntry(**entry)
            with self._lock:
                self._entries.append(history_entry)
                self._prune()
        except Exception as e:
            raise HistoryError(f"Failed to record history entry: {e}") from e

    def query(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._lock:
            results = list(self._entries)
        if filters:
            for key, value in filters.items():
                if key == "event_type":
                    results = [e for e in results if e.event_type == value]
                elif key == "state":
                    results = [e for e in results if e.state == value]
                elif key == "orchestration_id":
                    results = [e for e in results if e.orchestration_id == value]
                elif key == "since":
                    since = value if isinstance(value, datetime) else datetime.fromisoformat(value)
                    results = [e for e in results if e.started_at and e.started_at >= since]
        return [e.model_dump() for e in sorted(results, key=lambda x: x.started_at or datetime.min)]

    def _prune(self) -> None:
        if self._config.history_retention_days <= 0:
            return
        cutoff = datetime.utcnow() - timedelta(days=self._config.history_retention_days)
        self._entries = [e for e in self._entries if e.started_at is None or e.started_at >= cutoff]
