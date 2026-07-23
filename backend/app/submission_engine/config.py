from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SubmissionEngineConfig:
    version: str = "1.0.0"
    execution_mode: str = "dry_run"
    require_review_approval: bool = True
    require_workflow_ready: bool = True
    require_uploads_complete: bool = True
    require_manual_tasks_resolved: bool = True
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 5.0
    backoff_multiplier: float = 2.0
    max_retry_delay_seconds: float = 120.0
    step_timeout_ms: float = 30000.0
    submit_timeout_ms: float = 60000.0
    confirmation_timeout_ms: float = 15000.0
    screenshot_on_error: bool = True
    screenshot_on_success: bool = True
    track_metrics: bool = True
    generate_report: bool = True
    valid_execution_modes: tuple[str, ...] = ("dry_run", "manual_confirmation", "automatic", "safe_retry")
