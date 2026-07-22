from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OptimizationConfig:
    optimization_level: str = "balanced"
    ats_keyword_density_target: float = 0.02
    max_rewrite_intensity: float = 0.5
    cache_ttl_seconds: int = 300
    validation_strictness: str = "normal"
    max_bullet_points_per_experience: int = 5
    max_skills_to_include: int = 20

    def __post_init__(self) -> None:
        valid_levels = ("minimal", "balanced", "aggressive")
        if self.optimization_level not in valid_levels:
            raise ValueError(f"optimization_level must be one of {valid_levels}")
        valid_strictness = ("relaxed", "normal", "strict")
        if self.validation_strictness not in valid_strictness:
            raise ValueError(f"validation_strictness must be one of {valid_strictness}")
        if not 0.0 <= self.ats_keyword_density_target <= 1.0:
            raise ValueError("ats_keyword_density_target must be between 0 and 1")
        if not 0.0 <= self.max_rewrite_intensity <= 1.0:
            raise ValueError("max_rewrite_intensity must be between 0 and 1")
