from __future__ import annotations

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.deduplication import DeduplicationEngine
from app.jobs.filters import JobFilterChain
from app.jobs.normalization import JobNormalizer
from app.jobs.orchestration.search_ranking import RankingFactors, SearchRanking
from app.jobs.schemas import JobPosting, JobSearchRequest, JobSearchResponse, SearchMetadata

logger = structlog.get_logger(__name__)


class SearchAggregator:
    def __init__(
        self,
        config: JobDiscoveryConfig,
        ranker: SearchRanking | None = None,
        factors: RankingFactors | None = None,
    ) -> None:
        self._config = config
        self._normalizer = JobNormalizer()
        self._dedup = DeduplicationEngine(config)
        self._ranker = ranker or SearchRanking(factors)
        self._factors = factors

    def aggregate(
        self,
        provider_results: dict[str, list[JobPosting]],
        request: JobSearchRequest,
    ) -> JobSearchResponse:
        all_results: list[JobPosting] = []
        for _provider, postings in provider_results.items():
            if postings is not None:
                all_results.extend(postings)

        before_dedup = len(all_results)

        if request.deduplicate:
            all_results = self._dedup.deduplicate(all_results)

        after_dedup = len(all_results)
        duplicates_removed = before_dedup - after_dedup

        filter_chain = JobFilterChain.from_request(request)
        all_results = filter_chain.apply(all_results)

        all_results = self._ranker.rank(all_results, request, self._factors)

        total = len(all_results)
        paginated = all_results[request.offset : request.offset + request.limit]

        providers_queried = list(provider_results.keys())
        providers_succeeded = [
            p for p, results in provider_results.items() if results is not None
        ]
        providers_failed = [
            {"provider": p, "error": "No results returned"}
            for p, results in provider_results.items()
            if results is None
        ]

        metadata = SearchMetadata(
            total_results=total,
            returned_results=len(paginated),
            providers_queried=providers_queried,
            providers_succeeded=providers_succeeded,
            providers_failed=providers_failed,
            duplicates_removed=duplicates_removed,
            filters_applied=filter_chain.filter_names,
        )

        return JobSearchResponse(results=paginated, metadata=metadata)
