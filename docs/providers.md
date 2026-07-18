# Provider Framework Documentation

## Overview

The provider framework is a pluggable system for fetching job listings from multiple sources (job boards, ATS platforms, company career pages). It defines a common interface, handles rate limiting, retries, logging, and metrics, and normalizes all results into a unified schema.

## Architecture

```
app/services/providers/
├── __init__.py          # Public API exports
├── base.py              # BaseProvider ABC + RawJobData dataclass
├── registry.py          # ProviderRegistry (singleton)
├── factory.py           # ProviderFactory (singleton)
├── config.py            # ProviderSettings + PROVIDER_CONFIGS
├── errors.py            # ProviderError hierarchy (6 classes)
├── rate_limiter.py      # TokenBucketRateLimiter + RateLimiterRegistry
├── retry.py             # retry_async() + with_retry() decorator
├── request_manager.py   # HTTP client with rate limiting & auth
├── logging.py           # ProviderLogger (structlog wrapper)
├── metrics.py           # MetricsCollector (singleton)
├── health.py            # HealthStatus + health check functions
├── response.py          # ProviderSearchResult + AggregateSearchResult
├── utils.py             # parse_salary, parse_relative_date, clean_text, join_url
└── implementations/     # 17 provider implementations
    ├── linkedin.py
    ├── indeed.py
    ├── wellfound.py
    ├── greenhouse.py
    ├── lever.py
    ├── ashby.py
    ├── workday.py
    ├── google_jobs.py
    ├── remoteok.py
    ├── weworkremotely.py
    ├── career_pages.py
    ├── ycombinator.py         # Y Combinator Work at a Startup
    ├── naukri.py              # Naukri.com (India)
    ├── foundit.py             # Foundit.in (India)
    ├── internshala.py         # Internshala (India)
    ├── unstop.py              # Unstop (India)
    └── freshersworld.py       # Freshersworld (India)
```

## Provider Interface

Every provider extends `BaseProvider` (defined in `base.py`) and must implement:

- `name` property — unique string identifier (e.g., `"linkedin"`, `"greenhouse"`)
- `async def search(query, **kwargs) -> list[RawJobData]` — returns normalized job listings

```python
class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def search(self, query: str, **kwargs) -> list[RawJobData]: ...

    # Provided helpers:
    async def _request(self, method, url, **kwargs) -> httpx.Response
    async def _get_json(self, url, **kwargs) -> dict | list
    async def _get_html(self, url, **kwargs) -> BeautifulSoup
    async def close(self)
```

### RawJobData

The internal representation of a job listing:

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Job title |
| `company_name` | `str` | Company name |
| `location` | `str \| None` | Job location |
| `description` | `str \| None` | Full description |
| `url` | `str \| None` | Apply URL |
| `source` | `str` | Provider name |
| `source_job_id` | `str \| None` | Provider-specific ID |
| `salary_min` | `float \| None` | Minimum salary |
| `salary_max` | `float \| None` | Maximum salary |
| `salary_currency` | `str \| None` | Currency code |
| `salary_period` | `str \| None` | `yearly` / `monthly` / `hourly` |
| `posted_at` | `datetime \| None` | Posting date |
| `job_type` | `str \| None` | `full-time`, `contract`, etc. |
| `remote` | `bool` | Remote flag |
| `skills` | `list[str] \| None` | Extracted skills |
| `categories` | `list[str] \| None` | Category tags |
| `raw` | `dict \| None` | Raw provider data |

## Registry

`ProviderRegistry` manages all provider instances:

```python
registry = ProviderRegistry()
registry.register(linkedin_provider)
provider = registry.get("linkedin")
enabled = registry.get_enabled()       # only enabled providers
all_providers = registry.get_all()     # all registered
results = await registry.search_all("Python Developer")
```

A module-level singleton `provider_registry` is available.

## Factory

`ProviderFactory` creates provider instances from registered classes:

```python
factory = ProviderFactory()
factory.register_class("linkedin", LinkedInProvider)
provider = factory.create("linkedin")
all_providers = factory.create_all()  # creates all registered providers
```

A module-level singleton `get_provider_factory()` is available.

## Configuration

Each provider has a `ProviderSettings` dataclass defined in `config.py`:

| Field | Default | Description |
|---|---|---|
| `name` | `""` | Provider name |
| `enabled` | `True` | Whether enabled |
| `base_url` | `""` | API base URL |
| `api_key` | `None` | API key |
| `requests_per_second` | `2.0` | Rate limit |
| `max_retries` | `3` | Retry attempts |
| `timeout_seconds` | `30.0` | HTTP timeout |
| `extra_headers` | `{}` | Custom headers |
| `extra_params` | `{}` | Extra query params |

Predefined configs for all 17 providers live in `PROVIDER_CONFIGS`:

```python
PROVIDER_CONFIGS = {
    "linkedin": ProviderSettings(name="linkedin", base_url="https://www.linkedin.com/jobs/", ...),
    "indeed": ProviderSettings(name="indeed", base_url="https://www.indeed.com", ...),
    # ... all 11 providers
}
```

## Data Flow

```
User query
    │
    ▼
ProviderRegistry.search_all(query)
    │
    ├─► Provider A.search(query)
    │       ├─► RequestManager._request()
    │       │       ├─► RateLimiter.acquire()
    │       │       ├─► HTTP request (httpx)
    │       │       ├─► Error mapping
    │       │       └─► Retry on transient errors
    │       └─► Parse response → list[RawJobData]
    │
    ├─► Provider B.search(query) ...
    │
    ▼
AggregateSearchResult(jobs_by_provider, errors)
    │
    ▼
JobNormalizer.normalize(raw) → JobCreate (Pydantic)
    │
    ▼
JobDeduplicator.deduplicate(jobs) → (new_jobs, duplicates_removed)
    │
    ▼
Database (job_postings table)
```

## Rate Limiting

Uses a **token-bucket algorithm** (`TokenBucketRateLimiter` in `rate_limiter.py`):

- Each provider gets its own limiter (keyed by name)
- Tokens refill at `rate` tokens/second
- Burst capacity configured per provider
- `acquire()` blocks asynchronously until a token is available

## Retry Logic

`retry_async()` in `retry.py` retries on transient errors:

| Retryable | Non-retryable |
|---|---|
| `ProviderRateLimitError` | `ProviderAuthError` |
| `ProviderTimeoutError` | `ProviderParseError` |
| `ProviderUnavailableError` | Any non-ProviderError |
| `TimeoutError` | |
| `ConnectionError` | |

- Default: 3 retries, exponential backoff (1s base, 30s max)
- `with_retry` decorator wraps any async function

## Logging

`ProviderLogger` wraps structlog with provider context:

```python
logger = ProviderLogger("linkedin")
logger.info("search_started", query="Python Developer")
logger.request_summary("GET", url, 200, 450.0)
logger.search_summary("Python", 15, 1200.0)
```

## Metrics

`MetricsCollector` tracks per-provider counters:

```python
metrics = get_metrics_collector()
metrics.record_request("linkedin", success=True, duration_ms=450.0)
metrics.record_rate_limit("greenhouse")
metrics.record_jobs_found("indeed", 25)
summary = metrics.summary()  # returns dict of all provider metrics
metrics.reset()              # clears all counters
```

## Health Checks

`health.py` provides async health check functions:

```python
status = await check_provider_health(provider)   # single provider
results = await check_all_providers(registry)     # all registered
results = await check_enabled_providers(registry) # only enabled
```

`HealthStatus` fields: `name`, `available`, `latency_ms`, `error`, `enabled`, `last_success`

## Error Hierarchy

```
ProviderError (base)
├── ProviderAuthError       # Invalid/expired API key
├── ProviderRateLimitError  # Rate limited by provider
├── ProviderTimeoutError    # Request timed out
├── ProviderParseError      # Failed to parse response
└── ProviderUnavailableError # Service down/unreachable
```

## Utility Functions

All in `utils.py`:

- `parse_salary(text)` — parses `"$80K - $120K"`, `"€50/hr"`, `"£40,000"` → `(min, max, currency, period)`
- `parse_relative_date(text)` — parses `"3 days ago"`, `"Just posted"`, `"2 weeks ago"` → `datetime`
- `clean_text(text, max_length)` — strips HTML, collapses whitespace, truncates
- `join_url(base, path)` — safely joins URL parts
- `extract_emails(text)` — extracts email addresses
- `extract_urls(text)` — extracts URLs

## Response Models

```python
@dataclass
class ProviderSearchResult:
    provider: str
    jobs: list[RawJobData]
    error: str | None = None

@dataclass
class AggregateSearchResult:
    results: list[ProviderSearchResult]
    total_jobs: int
    providers_with_errors: list[str]
    all_jobs: list[RawJobData]
```

## Adding a New Provider

1. **Create the implementation file** in `implementations/`:

```python
from app.services.providers.base import BaseProvider, RawJobData

class MyProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "my_provider"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        data = await self._get_json(f"{self.settings.base_url}/jobs")
        return [
            RawJobData(title=item["title"], company_name=item["company"], ...)
            for item in data
        ]
```

2. **Add config** in `config.py` → `PROVIDER_CONFIGS`:

```python
"my_provider": ProviderSettings(name="my_provider", base_url="https://api.myprovider.com"),
```

3. **Register in the factory** in `factory.py`:

```python
self.register_class("my_provider", MyProvider)
```

4. **Export** in `__init__.py`.

5. **Add config validation** in `tests/test_provider_framework.py::TestProviderConfigs` and write provider-specific tests in `tests/test_providers_<region>.py`.

6. **Verify**:

```bash
cd backend
python -m pytest tests/test_provider_framework.py -k my_provider -v
ruff check app/services/providers/
```

## Testing

Test files:

- `tests/test_provider_framework.py` — core framework tests (75 tests)
- `tests/test_providers_india.py` — India & Y Combinator provider tests (53 tests)

Coverage:

- All 6 error classes and their hierarchy
- Rate limiter token acquisition and timing
- Provider registry CRUD and search
- Provider factory creation and singleton
- Request manager HTTP client creation
- Retry logic (success, exhaustion, non-retryable)
- Logger creation and methods
- Metrics recording, summary, and reset
- Health check functions
- Response dataclasses (search result, aggregate)
- All utility functions (salary, date, text, URL)
- Configuration validation for all 17 providers
- Provider-specific salary parsing (INR lakhs, stipends, yearly/monthly)
- Date parsing for Indian job portals
- Job ID extraction from URLs
- Location filtering parameter passthrough
- Factory registration and singleton for all new providers
- Job normalization for all new providers

Run tests:

```bash
cd backend
python -m pytest tests/test_provider_framework.py -v
python -m pytest tests/test_providers_india.py -v
# Or all together:
python -m pytest
```
