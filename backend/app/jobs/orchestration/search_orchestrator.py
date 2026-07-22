from __future__ import annotations

import asyncio
import time

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.orchestration.health_manager import ProviderHealthManager
from app.jobs.orchestration.provider_selector import ProviderSelector
from app.jobs.orchestration.search_aggregator import SearchAggregator
from app.jobs.orchestration.search_cache import SearchCache
from app.jobs.orchestration.search_metrics import SearchMetrics
from app.jobs.orchestration.search_ranking import RankingFactors
from app.jobs.registry import JobProviderRegistry
from app.jobs.schemas import JobPosting, JobSearchRequest, JobSearchResponse

logger = structlog.get_logger(__name__)


class SearchOrchestrator:
    def __init__(
        self,
        registry: JobProviderRegistry,
        config: JobDiscoveryConfig,
        selector: ProviderSelector | None = None,
        cache: SearchCache | None = None,
        metrics: SearchMetrics | None = None,
        health: ProviderHealthManager | None = None,
        ranker_factors: RankingFactors | None = None,
    ) -> None:
        self._registry = registry
        self._config = config
        self._selector = selector or ProviderSelector(registry, config)
        self._cache = cache or SearchCache(ttl_seconds=config.cache_ttl_seconds)
        self._metrics = metrics or SearchMetrics()
        self._health = health or ProviderHealthManager()
        self._aggregator = SearchAggregator(config, factors=ranker_factors)

    async def search(self, request: JobSearchRequest) -> JobSearchResponse:
        if self._cache:
            cached = self._cache.get(request)
            if cached is not None:
                logger.info("Search cache hit", query=request.query, providers=request.providers)
                if self._metrics:
                    self._metrics.record_search(
                        duration_ms=0,
                        provider_latencies={},
                        cache_hit=True,
                        jobs_before_dedup=0,
                        jobs_after_dedup=0,
                        provider_failures=[],
                        providers_queried=cached.metadata.providers_queried,
                    )
                return cached

        start = time.monotonic()
        provider_names = self._selector.select(request)
        logger.info(
            "Search started",
            query=request.query,
            providers_count=len(provider_names),
            providers=provider_names,
        )

        provider_results: dict[str, list[JobPosting] | None] = {}
        provider_latencies: dict[str, float] = {}
        provider_failures: list[str] = []

        semaphore = asyncio.Semaphore(self._config.max_concurrency)

        async def search_provider(name: str) -> tuple[str, list[JobPosting] | None, float]:
            async with semaphore:
                p_start = time.monotonic()
                try:
                    provider = self._registry.resolve(name)
                    response = await asyncio.wait_for(
                        provider.search_jobs(request),
                        timeout=self._config.provider_timeout_seconds,
                    )
                    p_elapsed = (time.monotonic() - p_start) * 1000
                    return name, response.results, p_elapsed
                except TimeoutError:
                    p_elapsed = (time.monotonic() - p_start) * 1000
                    logger.warning("Provider search timed out", provider=name)
                    return name, None, p_elapsed
                except Exception as exc:
                    p_elapsed = (time.monotonic() - p_start) * 1000
                    logger.error("Provider search failed", provider=name, error=str(exc))
                    return name, None, p_elapsed

        tasks = [search_provider(name) for name in provider_names]
        results = await asyncio.gather(*tasks)

        for name, result, p_elapsed in results:
            if result is not None:
                provider_results[name] = result
                provider_latencies[name] = p_elapsed
                self._health.record_success(name, p_elapsed)
            else:
                provider_results[name] = None
                provider_failures.append(name)
                self._health.record_failure(name, p_elapsed)

        elapsed_ms = (time.monotonic() - start) * 1000

        response = self._aggregator.aggregate(provider_results, request)
        response.metadata.duration_ms = int(elapsed_ms)

        if self._cache:
            self._cache.set(request, response)

        if self._metrics:
            jobs_before = sum(
                len(r) for r in provider_results.values() if r is not None
            )
            jobs_after = len(response.results)
            self._metrics.record_search(
                duration_ms=elapsed_ms,
                provider_latencies=provider_latencies,
                cache_hit=False,
                jobs_before_dedup=jobs_before,
                jobs_after_dedup=jobs_after,
                provider_failures=provider_failures,
                providers_queried=provider_names,
            )

        logger.info(
            "Search completed",
            query=request.query,
            duration_ms=int(elapsed_ms),
            results=response.metadata.returned_results,
            total=response.metadata.total_results,
            duplicates_removed=response.metadata.duplicates_removed,
            providers_succeeded=response.metadata.providers_succeeded,
            providers_failed=[f["provider"] for f in response.metadata.providers_failed],
        )

        return response

    def get_metrics_summary(self) -> dict:
        return self._metrics.summary() if self._metrics else {}

    def get_cache_stats(self) -> dict:
        return self._cache.stats() if self._cache else {}

    def get_health_summary(self) -> dict:
        return self._health.summary()

    def invalidate_cache(self, provider_name: str | None = None) -> int:
        return self._cache.invalidate(provider_name) if self._cache else 0
