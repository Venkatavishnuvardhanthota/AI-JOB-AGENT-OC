from __future__ import annotations

from threading import Lock
from typing import Any

from app.operations.config import OperationsConfig
from app.operations.interfaces import MetricsCollector
from app.operations.schemas import MetricPoint


class OperationsMetricsCollector(MetricsCollector):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config
        self._lock = Lock()
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._timings: dict[str, list[float]] = {}
        self._points: list[MetricPoint] = []

    def increment(self, name: str, value: float = 1.0, **tags: Any) -> None:
        key = self._key(name, tags)
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value
            self._record_point(name, value, tags)

    def gauge(self, name: str, value: float, **tags: Any) -> None:
        key = self._key(name, tags)
        with self._lock:
            self._gauges[key] = value
            self._record_point(name, value, tags)

    def timing(self, name: str, duration_ms: float, **tags: Any) -> None:
        key = self._key(name, tags)
        with self._lock:
            if key not in self._timings:
                self._timings[key] = []
            self._timings[key].append(duration_ms)
            if len(self._timings[key]) > self._config.metrics_buffer_size:
                self._timings[key].pop(0)
            self._record_point(name, duration_ms, tags)

    def get_metrics_snapshot(self) -> dict[str, Any]:
        with self._lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            timings = {}
            for key, values in self._timings.items():
                if values:
                    timings[key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                    }
            return {
                "counters": counters,
                "gauges": gauges,
                "timings": timings,
                "total_points": len(self._points),
            }

    def _key(self, name: str, tags: dict[str, Any]) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def _record_point(self, name: str, value: float, tags: dict[str, Any]) -> None:
        if len(self._points) >= self._config.metrics_buffer_size:
            self._points.pop(0)
        self._points.append(MetricPoint(name=name, value=value, tags=tags))
