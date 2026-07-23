from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OrchestratorConfig:
    max_retries_per_stage: int = 3
    retry_delay_seconds: float = 5.0
    backoff_multiplier: float = 2.0
    checkpoint_enabled: bool = True
    checkpoint_dir: str = ".orchestrator_checkpoints"
    strict_validation: bool = True
    max_concurrent_batch: int = 5
    execution_timeout_seconds: float = 7200.0
    report_ttl_seconds: int = 86400
    metrics_enabled: bool = True
    auto_create_workflow: bool = True
    auto_create_tracking: bool = True
    allowed_execution_modes: tuple[str, ...] = (
        "single", "batch", "scheduled", "manual", "dry_run",
    )
