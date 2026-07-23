from __future__ import annotations

from functools import lru_cache

from app.review.config import ReviewConfig
from app.review.service import ReviewService


@lru_cache
def _get_config() -> ReviewConfig:
    return ReviewConfig()


@lru_cache
def get_review_service() -> ReviewService:
    return ReviewService(config=_get_config())
