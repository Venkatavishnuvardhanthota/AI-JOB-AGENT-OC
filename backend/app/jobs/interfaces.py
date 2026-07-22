from __future__ import annotations

from abc import ABC, abstractmethod

from app.jobs.config import JobDiscoveryConfig
from app.jobs.schemas import JobProviderInfo, JobSearchRequest, JobSearchResponse


class JobProvider(ABC):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"
    supports_pagination: bool = False
    supports_filters: bool = False

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.config = config

    @abstractmethod
    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    @abstractmethod
    async def provider_info(self) -> JobProviderInfo: ...
