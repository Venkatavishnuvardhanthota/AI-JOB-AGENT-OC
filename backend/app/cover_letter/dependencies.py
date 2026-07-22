from __future__ import annotations

from functools import lru_cache

from app.cover_letter.config import CoverLetterConfig
from app.cover_letter.service import CoverLetterGenerationService


@lru_cache
def _get_config() -> CoverLetterConfig:
    return CoverLetterConfig(
        cache_ttl_seconds=300,
    )


@lru_cache
def get_cover_letter_service() -> CoverLetterGenerationService:
    return CoverLetterGenerationService(config=_get_config())
