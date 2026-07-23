from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PackageConfig:
    version: str = "1.0.0"
    cache_ttl_seconds: int = 300
    strict_validation: bool = True

    completeness_weight_job: float = 0.15
    completeness_weight_profile: float = 0.15
    completeness_weight_ai: float = 0.10
    completeness_weight_match: float = 0.10
    completeness_weight_resume: float = 0.25
    completeness_weight_cover_letter: float = 0.25

    def __post_init__(self) -> None:
        total = (
            self.completeness_weight_job
            + self.completeness_weight_profile
            + self.completeness_weight_ai
            + self.completeness_weight_match
            + self.completeness_weight_resume
            + self.completeness_weight_cover_letter
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Completeness weights must sum to 1.0, got {total}")
