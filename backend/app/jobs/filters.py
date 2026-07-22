from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import structlog

from app.jobs.schemas import (
    EmploymentType,
    ExperienceLevel,
    JobPosting,
    JobSearchRequest,
    RemoteType,
)

logger = structlog.get_logger(__name__)


class JobFilter(ABC):
    name: str

    @abstractmethod
    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        ...


class KeywordFilter(JobFilter):
    name = "keyword"

    def __init__(self, keywords: list[str]) -> None:
        self._keywords = [k.lower().strip() for k in keywords if k.strip()]

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        if not self._keywords:
            return postings
        result = []
        for posting in postings:
            text = f"{posting.title} {posting.company.name} {posting.description or ''}".lower()
            if any(kw in text for kw in self._keywords):
                result.append(posting)
        return result


class LocationFilter(JobFilter):
    name = "location"

    def __init__(self, location: str) -> None:
        self._location = location.lower().strip()

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        if not self._location:
            return postings
        result = []
        for posting in postings:
            text = (
                f"{posting.location.city or ''} {posting.location.state or ''} "
                f"{posting.location.country or ''} {posting.location.display_name or ''}"
            ).lower()
            if self._location in text:
                result.append(posting)
        return result


class RemoteFilter(JobFilter):
    name = "remote"

    def __init__(self, remote_only: bool) -> None:
        self._remote_only = remote_only

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        if not self._remote_only:
            return postings
        return [p for p in postings if p.location.remote_type == RemoteType.REMOTE]


class ExperienceLevelFilter(JobFilter):
    name = "experience_level"

    def __init__(self, level: ExperienceLevel) -> None:
        self._level = level

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        return [p for p in postings if p.experience_level == self._level]


class EmploymentTypeFilter(JobFilter):
    name = "employment_type"

    def __init__(self, emp_type: EmploymentType) -> None:
        self._type = emp_type

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        return [p for p in postings if p.employment_type == self._type]


class SalaryRangeFilter(JobFilter):
    name = "salary_range"

    def __init__(self, min_amount: float | None, max_amount: float | None) -> None:
        self._min = min_amount
        self._max = max_amount

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        if self._min is None and self._max is None:
            return postings
        result = []
        for posting in postings:
            sal = posting.salary
            if sal is None:
                if self._min is None:
                    result.append(posting)
                continue
            if self._min is not None and (sal.max_amount or sal.min_amount or 0) < self._min:
                continue
            if self._max is not None and (sal.min_amount or 0) > self._max:
                continue
            result.append(posting)
        return result


class PostedWithinFilter(JobFilter):
    name = "posted_within_days"

    def __init__(self, days: int) -> None:
        self._cutoff = datetime.utcnow() - timedelta(days=days)

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        return [
            p
            for p in postings
            if p.posted_date is None or p.posted_date >= self._cutoff
        ]


class JobFilterChain:
    def __init__(self) -> None:
        self._filters: list[JobFilter] = []

    def add(self, filter_: JobFilter) -> None:
        self._filters.append(filter_)

    def apply(self, postings: list[JobPosting]) -> list[JobPosting]:
        result = postings
        for f in self._filters:
            result = f.apply(result)
        return result

    @property
    def filter_names(self) -> list[str]:
        return [f.name for f in self._filters]

    @classmethod
    def from_request(cls, request: JobSearchRequest) -> JobFilterChain:
        chain = cls()
        if request.keywords:
            chain.add(KeywordFilter(request.keywords))
        if request.query:
            chain.add(KeywordFilter([request.query]))
        if request.location:
            chain.add(LocationFilter(request.location))
        if request.remote_only is not None:
            chain.add(RemoteFilter(request.remote_only))
        if request.experience_level is not None:
            chain.add(ExperienceLevelFilter(request.experience_level))
        if request.employment_type is not None:
            chain.add(EmploymentTypeFilter(request.employment_type))
        if request.salary_min is not None or request.salary_max is not None:
            chain.add(SalaryRangeFilter(request.salary_min, request.salary_max))
        if request.posted_within_days is not None:
            chain.add(PostedWithinFilter(request.posted_within_days))
        return chain
