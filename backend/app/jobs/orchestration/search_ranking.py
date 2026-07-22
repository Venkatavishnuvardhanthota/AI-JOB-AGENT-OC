from __future__ import annotations

from datetime import datetime, timezone

import structlog

from app.jobs.schemas import JobPosting, JobSearchRequest, RemoteType

logger = structlog.get_logger(__name__)


class RankingFactors:
    def __init__(
        self,
        freshness_weight: float = 0.25,
        salary_weight: float = 0.20,
        remote_weight: float = 0.15,
        keyword_weight: float = 0.25,
        provider_weight: float = 0.15,
        provider_quality: dict[str, float] | None = None,
    ) -> None:
        self.freshness_weight = freshness_weight
        self.salary_weight = salary_weight
        self.remote_weight = remote_weight
        self.keyword_weight = keyword_weight
        self.provider_weight = provider_weight
        self.provider_quality = provider_quality or {}

    def merge(self, overrides: dict) -> RankingFactors:
        kwargs = {
            "freshness_weight": overrides.get("freshness_weight", self.freshness_weight),
            "salary_weight": overrides.get("salary_weight", self.salary_weight),
            "remote_weight": overrides.get("remote_weight", self.remote_weight),
            "keyword_weight": overrides.get("keyword_weight", self.keyword_weight),
            "provider_weight": overrides.get("provider_weight", self.provider_weight),
            "provider_quality": overrides.get("provider_quality", self.provider_quality),
        }
        return RankingFactors(**kwargs)

    def to_dict(self) -> dict:
        return {
            "freshness_weight": self.freshness_weight,
            "salary_weight": self.salary_weight,
            "remote_weight": self.remote_weight,
            "keyword_weight": self.keyword_weight,
            "provider_weight": self.provider_weight,
        }


DEFAULT_RANKING_FACTORS = RankingFactors()


class SearchRanking:
    def __init__(self, factors: RankingFactors | None = None) -> None:
        self._factors = factors or DEFAULT_RANKING_FACTORS

    def rank(
        self,
        postings: list[JobPosting],
        request: JobSearchRequest,
        factors: RankingFactors | None = None,
    ) -> list[JobPosting]:
        f = factors or self._factors
        keywords = self._get_keywords(request)
        now = datetime.now(timezone.utc)

        scored = []
        for posting in postings:
            score = self._score(posting, request, keywords, f, now)
            scored.append((score, posting))

        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored]

    def _get_keywords(self, request: JobSearchRequest) -> list[str]:
        words: list[str] = []
        if request.query:
            words.extend(request.query.lower().split())
        if request.keywords:
            words.extend(k.lower() for k in request.keywords)
        return words

    def _score(
        self,
        posting: JobPosting,
        request: JobSearchRequest,
        keywords: list[str],
        factors: RankingFactors,
        now: datetime,
    ) -> float:
        total = 0.0

        total += self._freshness_score(posting, now) * factors.freshness_weight
        total += self._salary_score(posting) * factors.salary_weight
        total += self._remote_score(posting, request) * factors.remote_weight
        total += self._keyword_score(posting, keywords) * factors.keyword_weight
        total += self._provider_quality_score(posting, factors) * factors.provider_weight

        return total

    def _freshness_score(self, posting: JobPosting, now: datetime) -> float:
        if posting.posted_date is None:
            return 0.5
        posted = posting.posted_date
        if posted.tzinfo is None and now.tzinfo is not None:
            posted = posted.replace(tzinfo=now.tzinfo)
        elif posted.tzinfo is not None and now.tzinfo is None:
            posted = posted.replace(tzinfo=None)
        delta = now - posted
        days = delta.total_seconds() / 86400.0
        if days < 0:
            return 1.0
        return max(0.0, 1.0 - (days / 30.0))

    def _salary_score(self, posting: JobPosting) -> float:
        if posting.salary is None:
            return 0.0
        return 1.0

    def _remote_score(self, posting: JobPosting, request: JobSearchRequest) -> float:
        if request.remote_only and posting.location.remote_type == RemoteType.REMOTE:
            return 1.0
        if posting.location.remote_type == RemoteType.REMOTE:
            return 0.5
        return 0.0

    def _keyword_score(self, posting: JobPosting, keywords: list[str]) -> float:
        if not keywords:
            return 0.5

        text = " ".join([
            posting.title.lower(),
            posting.company.name.lower(),
            posting.description or "",
            " ".join(posting.skills),
        ])

        matches = sum(1 for kw in keywords if kw in text)
        return min(1.0, matches / max(len(keywords), 1))

    def _provider_quality_score(self, posting: JobPosting, factors: RankingFactors) -> float:
        return factors.provider_quality.get(posting.provider, 1.0)
