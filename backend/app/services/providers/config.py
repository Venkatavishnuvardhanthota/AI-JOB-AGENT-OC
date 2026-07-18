from dataclasses import dataclass, field


@dataclass
class ProviderSettings:
    """Configuration for a single provider."""

    name: str
    enabled: bool = True
    base_url: str = ""
    api_key: str | None = None
    requests_per_second: float = 1.0
    max_retries: int = 3
    timeout_seconds: float = 30.0
    extra_headers: dict[str, str] = field(default_factory=dict)
    extra_params: dict[str, str] = field(default_factory=dict)


PROVIDER_CONFIGS: dict[str, ProviderSettings] = {
    "linkedin": ProviderSettings(
        name="linkedin",
        base_url="https://www.linkedin.com/jobs",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "indeed": ProviderSettings(
        name="indeed",
        base_url="https://www.indeed.com",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "wellfound": ProviderSettings(
        name="wellfound",
        base_url="https://wellfound.com",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "greenhouse": ProviderSettings(
        name="greenhouse",
        base_url="https://boards-api.greenhouse.io/v1/boards",
        requests_per_second=5.0,
        max_retries=3,
        timeout_seconds=15.0,
    ),
    "lever": ProviderSettings(
        name="lever",
        base_url="https://api.lever.co/v0/postings",
        requests_per_second=5.0,
        max_retries=3,
        timeout_seconds=15.0,
    ),
    "ashby": ProviderSettings(
        name="ashby",
        base_url="https://api.ashbyhq.com/posting-api/job-board",
        requests_per_second=5.0,
        max_retries=3,
        timeout_seconds=15.0,
    ),
    "workday": ProviderSettings(
        name="workday",
        base_url="",
        requests_per_second=2.0,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "google_jobs": ProviderSettings(
        name="google_jobs",
        base_url="https://www.google.com/search",
        requests_per_second=0.3,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "remoteok": ProviderSettings(
        name="remoteok",
        base_url="https://remoteok.com",
        requests_per_second=2.0,
        max_retries=3,
        timeout_seconds=15.0,
    ),
    "weworkremotely": ProviderSettings(
        name="weworkremotely",
        base_url="https://weworkremotely.com",
        requests_per_second=1.0,
        max_retries=2,
        timeout_seconds=20.0,
    ),
    "career_pages": ProviderSettings(
        name="career_pages",
        base_url="",
        requests_per_second=1.0,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "ycombinator": ProviderSettings(
        name="ycombinator",
        base_url="https://www.workatastartup.com",
        requests_per_second=2.0,
        max_retries=3,
        timeout_seconds=15.0,
    ),
    "naukri": ProviderSettings(
        name="naukri",
        base_url="https://www.naukri.com",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "foundit": ProviderSettings(
        name="foundit",
        base_url="https://www.foundit.in",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "internshala": ProviderSettings(
        name="internshala",
        base_url="https://internshala.com",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "unstop": ProviderSettings(
        name="unstop",
        base_url="https://unstop.com",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
    "freshersworld": ProviderSettings(
        name="freshersworld",
        base_url="https://www.freshersworld.com",
        requests_per_second=0.5,
        max_retries=2,
        timeout_seconds=30.0,
    ),
}


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
