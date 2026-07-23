from __future__ import annotations

import uuid
from datetime import datetime
from threading import Lock
from typing import Any

from app.operations.config import OperationsConfig
from app.operations.exceptions import TracingError
from app.operations.interfaces import Tracer
from app.operations.schemas import TraceEntry


class OperationsTracer(Tracer):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config
        self._lock = Lock()
        self._traces: dict[str, list[TraceEntry]] = {}
        self._active_spans: dict[str, TraceEntry] = {}

    def start_span(
        self,
        name: str,
        trace_id: str,
        parent_id: str | None = None,
        **tags: Any,
    ) -> str:
        span_id = str(uuid.uuid4())
        entry = TraceEntry(
            span_id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            tags=tags,
        )
        with self._lock:
            if trace_id not in self._traces:
                self._traces[trace_id] = []
            if len(self._traces[trace_id]) >= self._config.max_trace_entries:
                raise TracingError(f"Trace '{trace_id}' exceeds max entries")
            self._traces[trace_id].append(entry)
            self._active_spans[span_id] = entry
        return span_id

    def end_span(self, span_id: str, **tags: Any) -> None:
        with self._lock:
            entry = self._active_spans.pop(span_id, None)
            if entry is None:
                raise TracingError(f"Span '{span_id}' not found or already ended")
            entry.ended_at = datetime.utcnow()
            if entry.started_at:
                entry.duration_ms = (entry.ended_at - entry.started_at).total_seconds() * 1000
            entry.tags.update(tags)

    def get_trace(self, trace_id: str) -> list[dict[str, Any]] | None:
        with self._lock:
            entries = self._traces.get(trace_id)
            if entries is None:
                return None
            return [e.model_dump() for e in entries]
