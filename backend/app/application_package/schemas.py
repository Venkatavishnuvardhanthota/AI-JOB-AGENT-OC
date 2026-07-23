from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PackageStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    INCOMPLETE = "incomplete"


class PackageValidation(BaseModel):
    all_inputs_present: bool = False
    has_job_posting: bool = False
    has_profile: bool = False
    has_application_intelligence: bool = False
    has_match_result: bool = False
    has_resume: bool = False
    has_cover_letter: bool = False
    job_consistency_ok: bool = False
    profile_consistency_ok: bool = False
    company_name_consistency_ok: bool | None = None
    stale_profile_data: bool = False
    mismatched_job_hash: bool = False
    mismatched_profile_hash: bool = False
    warnings: list[str] = Field(default_factory=list)


class ApplicationPackage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"

    profile_hash: str | None = None
    job_hash: str | None = None
    resume_hash: str | None = None
    cover_letter_hash: str | None = None
    match_result_hash: str | None = None

    job: Any = None
    profile: Any = None
    application_intelligence: Any = None
    match_result: Any = None
    resume: Any = None
    cover_letter: Any = None

    validation: PackageValidation = Field(default_factory=PackageValidation)
    completeness_score: int = Field(default=0, ge=0, le=100)
    status: PackageStatus = PackageStatus.INCOMPLETE

    warnings: list[str] = Field(default_factory=list)
