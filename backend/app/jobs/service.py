from __future__ import annotations

import time

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.deduplication import DeduplicationEngine
from app.jobs.exceptions import ProviderNotFoundError, SearchValidationError
from app.jobs.filters import JobFilterChain
from app.jobs.registry import JobProviderRegistry
from app.jobs.schemas import (
    JobProviderInfo,
    JobSearchRequest,
    JobSearchResponse,
    SearchMetadata,
)

logger = structlog.get_logger(__name__)


class JobDiscoveryService:
    def __init__(
        self,
        registry: JobProviderRegistry,
        config: JobDiscoveryConfig,
    ) -> None:
        self._registry = registry
        self._config = config
        self._dedup = DeduplicationEngine(config)

    async def search(self, request: JobSearchRequest) -> JobSearchResponse:
        self._validate(request)
        providers_to_query = self._resolve_providers(request.providers)
        metadata = SearchMetadata(
            providers_queried=providers_to_query,
        )
        start = time.monotonic()

        all_results: list = []
        for name in providers_to_query:
            try:
                provider = self._registry.resolve(name)
                response = await provider.search_jobs(request)
                all_results.extend(response.results)
                metadata.providers_succeeded.append(name)
            except ProviderNotFoundError:
                metadata.providers_failed.append({"provider": name, "error": "Not registered"})
                logger.warning("Provider not found in registry", provider=name)
            except Exception as exc:
                metadata.providers_failed.append({"provider": name, "error": str(exc)})
                logger.error("Provider search failed", provider=name, error=str(exc))

        if request.deduplicate:
            before = len(all_results)
            all_results = self._dedup.deduplicate(all_results)
            metadata.duplicates_removed = before - len(all_results)

        filter_chain = JobFilterChain.from_request(request)
        all_results = filter_chain.apply(all_results)
        metadata.filters_applied = filter_chain.filter_names

        total = len(all_results)
        paginated = all_results[request.offset : request.offset + request.limit]
        metadata.total_results = total
        metadata.returned_results = len(paginated)
        metadata.duration_ms = int((time.monotonic() - start) * 1000)

        return JobSearchResponse(results=paginated, metadata=metadata)

    async def search_all(self, request: JobSearchRequest) -> JobSearchResponse:
        return await self.search(request)

    async def health_check(self, provider_name: str | None = None) -> dict[str, bool]:
        targets = [provider_name] if provider_name else self._registry.list_providers()
        results: dict[str, bool] = {}
        for name in targets:
            try:
                provider = self._registry.resolve(name)
                is_healthy = await provider.health_check()
                results[name] = is_healthy
            except ProviderNotFoundError:
                results[name] = False
            except Exception:
                logger.exception("Health check failed for provider", provider=name)
                results[name] = False
        return results

    async def provider_info(self, provider_name: str) -> JobProviderInfo:
        provider = self._registry.resolve(provider_name)
        return await provider.provider_info()

    def list_providers(self) -> list[str]:
        return self._registry.list_providers()

    def _validate(self, request: JobSearchRequest) -> None:
        if not request.query and not request.keywords:
            raise SearchValidationError("At least one of 'query' or 'keywords' must be provided.")

    def _resolve_providers(self, requested: list[str] | None) -> list[str]:
        if requested:
            for name in requested:
                if not self._registry.is_registered(name):
                    raise ProviderNotFoundError(f"Requested provider '{name}' is not registered.")
            return requested[:]
        registered = self._registry.list_providers()
        enabled = self._config.enabled_providers
        if enabled:
            return [p for p in registered if p in enabled]
        return registered
