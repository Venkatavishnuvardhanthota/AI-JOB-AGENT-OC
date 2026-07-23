from __future__ import annotations

from threading import Lock

from app.workflow.schemas import HistoryEntry


class WorkflowHistory:
    def __init__(self) -> None:
        self._entries: dict[str, list[HistoryEntry]] = {}
        self._lock = Lock()

    def add(self, workflow_id: str, entry: HistoryEntry) -> None:
        with self._lock:
            if workflow_id not in self._entries:
                self._entries[workflow_id] = []
            self._entries[workflow_id].append(entry)

    def get_history(self, workflow_id: str) -> list[HistoryEntry]:
        with self._lock:
            return list(self._entries.get(workflow_id, []))

    def clear(self, workflow_id: str | None = None) -> None:
        with self._lock:
            if workflow_id:
                self._entries.pop(workflow_id, None)
            else:
                self._entries.clear()

    def get_latest(self, workflow_id: str) -> HistoryEntry | None:
        with self._lock:
            entries = self._entries.get(workflow_id, [])
            if entries:
                return entries[-1]
            return None

    def count(self, workflow_id: str) -> int:
        with self._lock:
            return len(self._entries.get(workflow_id, []))
