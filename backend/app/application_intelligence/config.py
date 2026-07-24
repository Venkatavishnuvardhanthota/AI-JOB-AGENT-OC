from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApplicationIntelligenceConfig:
    startup_keywords: tuple[str, ...] = (
        "startup",
        "seed",
        "series a",
        "series b",
        "venture-backed",
        "high-growth",
        "fast-paced",
        "scale-up",
        "unicorn",
    )
    enterprise_keywords: tuple[str, ...] = (
        "enterprise",
        "fortune",
        "global",
        "multinational",
        "corporate",
        "established",
        "large-scale",
        "inc.",
    )
    seniority_keywords: dict[str, tuple[str, ...]] = None

    confidence_score_fields: int = 7
    high_priority_threshold: float = 0.75
    medium_priority_threshold: float = 0.45

    cache_ttl_seconds: int = 300
    strict_validation: bool = True

    def __post_init__(self) -> None:
        if self.seniority_keywords is None:
            self.seniority_keywords = {
                "entry": ("junior", "entry", "graduate", "trainee", "intern", "fresher"),
                "mid": ("mid", "mid-level", "intermediate", "staff"),
                "senior": ("senior", "sr", "sr.", "lead", "principal", "staff"),
                "executive": ("vp", "vice president", "director", "head of", "chief", "cto", "ceo"),
            }
