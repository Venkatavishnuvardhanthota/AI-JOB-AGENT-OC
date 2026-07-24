from __future__ import annotations

import time
from datetime import datetime
from threading import Lock

from app.automation.config import AutomationConfig
from app.automation.schemas import AutomationPolicy


class PolicyEnforcer:
    def __init__(self, config: AutomationConfig) -> None:
        self._config = config
        self._active_jobs: set[str] = set()
        self._execution_timestamps: list[float] = []
        self._lock = Lock()

    def check_concurrent_jobs(self, policy: AutomationPolicy) -> bool:
        max_concurrent = policy.max_concurrent_jobs or self._config.max_concurrent_jobs
        with self._lock:
            return len(self._active_jobs) < max_concurrent

    def acquire_job_slot(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._active_jobs:
                return False
            max_concurrent = self._config.max_concurrent_jobs
            if len(self._active_jobs) >= max_concurrent:
                return False
            self._active_jobs.add(job_id)
            return True

    def release_job_slot(self, job_id: str) -> None:
        with self._lock:
            self._active_jobs.discard(job_id)

    def is_in_quiet_hours(self, policy: AutomationPolicy) -> bool:
        start = policy.quiet_hours_start or self._config.quiet_hours_start
        end = policy.quiet_hours_end or self._config.quiet_hours_end
        if start is None or end is None:
            return False
        now = datetime.utcnow()
        now_mins = now.hour * 60 + now.minute
        start_parts = start.split(":")
        end_parts = end.split(":")
        start_mins = int(start_parts[0]) * 60 + int(start_parts[1]) if len(start_parts) > 1 else 0
        end_mins = int(end_parts[0]) * 60 + int(end_parts[1]) if len(end_parts) > 1 else 0
        if start_mins <= end_mins:
            return start_mins <= now_mins <= end_mins
        return now_mins >= start_mins or now_mins <= end_mins

    def check_rate_limit(self, policy: AutomationPolicy) -> bool:
        max_per_minute = policy.rate_limit_per_minute or self._config.rate_limit_per_minute
        now = time.monotonic()
        with self._lock:
            self._execution_timestamps = [t for t in self._execution_timestamps if now - t < 60.0]
            if len(self._execution_timestamps) >= max_per_minute:
                return False
            self._execution_timestamps.append(now)
            return True

    def should_auto_approve(self, policy: AutomationPolicy, score: float) -> bool:
        if policy.auto_approve_threshold is None:
            return False
        return score >= policy.auto_approve_threshold

    def get_active_job_count(self) -> int:
        with self._lock:
            return len(self._active_jobs)

    def reset(self) -> None:
        with self._lock:
            self._active_jobs.clear()
            self._execution_timestamps.clear()
