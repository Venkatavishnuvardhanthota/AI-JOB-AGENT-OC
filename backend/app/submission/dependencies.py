from __future__ import annotations

from functools import lru_cache

from app.submission.config import SubmissionConfig
from app.submission.service import SubmissionService


@lru_cache
def _get_config() -> SubmissionConfig:
    return SubmissionConfig()


@lru_cache
def get_submission_service() -> SubmissionService:
    return SubmissionService(config=_get_config())
