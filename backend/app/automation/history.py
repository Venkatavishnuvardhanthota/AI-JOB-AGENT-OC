from __future__ import annotations

from datetime import datetime
from threading import Lock

from app.automation.schemas import ExecutionRecord, HistoryQuery


class ExecutionHistory:
    def __init__(self, max_records: int = 10000) -> None:
        self._records: list[ExecutionRecord] = []
        self._max_records = max_records
        self._lock = Lock()

    def record(self, entry: ExecutionRecord) -> None:
        with self._lock:
            self._records.append(entry)
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records:]

    def get(self, execution_id: str) -> ExecutionRecord | None:
        with self._lock:
            for r in self._records:
                if r.id == execution_id:
                    return r
            return None

    def query(self, query: HistoryQuery) -> list[ExecutionRecord]:
        with self._lock:
            results = list(self._records)
            if query.job_id is not None:
                results = [r for r in results if r.job_id == query.job_id]
            if query.status is not None:
                results = [r for r in results if r.status == query.status]
            results.sort(key=lambda r: r.started_at or datetime.min, reverse=True)
            return results[query.offset:query.offset + query.limit]

    def list_by_job(self, job_id: str) -> list[ExecutionRecord]:
        with self._lock:
            return sorted(
                [r for r in self._records if r.job_id == job_id],
                key=lambda r: r.started_at or datetime.min,
                reverse=True,
            )

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._records)
