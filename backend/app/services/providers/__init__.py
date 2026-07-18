"""Provider framework for job board integrations."""

from app.services.providers.base import BaseProvider, RawJobData
from app.services.providers.config import PROVIDER_CONFIGS, ProviderSettings
from app.services.providers.errors import (
    ProviderAuthError,
    ProviderError,
    ProviderParseError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.services.providers.factory import ProviderFactory, get_provider_factory
from app.services.providers.health import (
    HealthStatus,
    check_all_providers,
    check_enabled_providers,
    check_provider_health,
)
from app.services.providers.logging import ProviderLogger
from app.services.providers.metrics import MetricsCollector, get_metrics_collector
from app.services.providers.rate_limiter import RateLimiterRegistry, TokenBucketRateLimiter
from app.services.providers.registry import ProviderNotFoundError, ProviderRegistry, provider_registry
from app.services.providers.request_manager import RequestManager
from app.services.providers.response import AggregateSearchResult, ProviderSearchResult
from app.services.providers.retry import retry_async, with_retry
from app.services.providers.utils import clean_text, join_url, parse_relative_date, parse_salary

__all__ = [
    "BaseProvider",
    "RawJobData",
    "ProviderSettings",
    "PROVIDER_CONFIGS",
    "ProviderError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderParseError",
    "ProviderUnavailableError",
    "ProviderFactory",
    "get_provider_factory",
    "HealthStatus",
    "check_all_providers",
    "check_enabled_providers",
    "check_provider_health",
    "ProviderLogger",
    "MetricsCollector",
    "get_metrics_collector",
    "TokenBucketRateLimiter",
    "RateLimiterRegistry",
    "ProviderRegistry",
    "provider_registry",
    "ProviderNotFoundError",
    "RequestManager",
    "AggregateSearchResult",
    "ProviderSearchResult",
    "retry_async",
    "with_retry",
    "parse_salary",
    "parse_relative_date",
    "clean_text",
    "join_url",
]
