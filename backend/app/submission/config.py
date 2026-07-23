from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SubmissionConfig:
    cache_ttl_seconds: int = 300
    strict_validation: bool = True
    dry_run_enabled: bool = True
    default_max_retries: int = 3
    default_retry_delay_seconds: float = 60.0
    retry_backoff_multiplier: float = 2.0
    max_concurrent_submissions: int = 5
    queue_poll_interval_seconds: float = 10.0
