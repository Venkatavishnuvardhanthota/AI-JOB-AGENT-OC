from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AutomationConfig:
    cache_ttl_seconds: int = 300
    strict_validation: bool = True
    default_max_retries: int = 3
    max_concurrent_jobs: int = 5
    execution_timeout_seconds: float = 3600.0
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    rate_limit_per_minute: int = 10
    max_queue_size: int = 1000
