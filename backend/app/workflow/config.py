from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkflowConfig:
    cache_ttl_seconds: int = 300
    strict_validation: bool = True
    max_retries: int = 3
    allow_rollback: bool = True
    track_history: bool = True
