from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApplicationTrackingConfig:
    cache_ttl_seconds: int = 300
    strict_validation: bool = True
    track_timeline: bool = True
    auto_calculate_metrics: bool = True
    max_timeline_events: int = 1000
