from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OperationsConfig:
    log_level: str = "INFO"
    trace_enabled: bool = True
    metrics_enabled: bool = True
    health_check_interval_seconds: int = 60
    diagnostics_enabled: bool = True
    history_retention_days: int = 90
    export_dir: str = ".operations_exports"
    max_trace_entries: int = 10000
    slow_stage_threshold_ms: float = 30000.0
    high_retry_threshold: int = 3
    metrics_buffer_size: int = 1000
