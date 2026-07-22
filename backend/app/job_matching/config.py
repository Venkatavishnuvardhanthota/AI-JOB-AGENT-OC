from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MatchingConfig:
    skills_weight: float = 0.25
    experience_weight: float = 0.18
    education_weight: float = 0.10
    location_weight: float = 0.08
    remote_weight: float = 0.06
    salary_weight: float = 0.08
    employment_type_weight: float = 0.06
    career_level_weight: float = 0.07
    industry_weight: float = 0.05
    certifications_weight: float = 0.04
    projects_weight: float = 0.03

    min_recommendation_threshold: float = 30.0
    strong_apply_threshold: float = 80.0
    apply_threshold: float = 60.0
    consider_threshold: float = 40.0

    cache_ttl_seconds: int = 300

    high_confidence_threshold: float = 80.0
    medium_confidence_threshold: float = 50.0

    skills_min_match_percentage: float = 0.3
    skills_expert_bonus: float = 5.0
    experience_years_tolerance: float = 2.0
    salary_tolerance_percentage: float = 0.2
    location_distance_km: float = 50.0

    def __post_init__(self) -> None:
        total = (
            self.skills_weight
            + self.experience_weight
            + self.education_weight
            + self.location_weight
            + self.remote_weight
            + self.salary_weight
            + self.employment_type_weight
            + self.career_level_weight
            + self.industry_weight
            + self.certifications_weight
            + self.projects_weight
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"MatchingConfig weights must sum to 1.0, got {total}")
