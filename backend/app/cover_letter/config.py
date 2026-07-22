from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CoverLetterConfig:
    tone: str = "professional"
    length: str = "medium"
    creativity: float = 0.3
    template_style: str = "general"
    cache_ttl_seconds: int = 300
    strict_validation: bool = True
    max_paragraph_length: int = 300
    min_paragraph_length: int = 50

    def __post_init__(self) -> None:
        valid_tones = ("professional", "enthusiastic", "formal", "casual")
        if self.tone not in valid_tones:
            raise ValueError(f"tone must be one of {valid_tones}")
        valid_lengths = ("short", "medium", "long")
        if self.length not in valid_lengths:
            raise ValueError(f"length must be one of {valid_lengths}")
        if not 0.0 <= self.creativity <= 1.0:
            raise ValueError("creativity must be between 0 and 1")
