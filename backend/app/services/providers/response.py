"""Common provider response objects and envelope models."""

from dataclasses import dataclass, field

from app.services.providers.base import RawJobData


@dataclass
class ProviderSearchResult:
    """Result of a provider search operation."""

    provider: str
    jobs: list[RawJobData] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    duration_ms: float = 0.0
    query: str = ""


@dataclass
class AggregateSearchResult:
    """Aggregated results from multiple providers."""

    results: list[ProviderSearchResult] = field(default_factory=list)
    total_jobs: int = 0
    total_duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    def all_jobs(self) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        for r in self.results:
            jobs.extend(r.jobs)
        return jobs

    def providers_with_errors(self) -> list[str]:
        return [r.provider for r in self.results if not r.success]

    def successful_providers(self) -> list[str]:
        return [r.provider for r in self.results if r.success]
