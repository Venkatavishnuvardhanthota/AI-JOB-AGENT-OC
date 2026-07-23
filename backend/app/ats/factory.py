from __future__ import annotations

from typing import Any

import structlog

from app.ats.config import ATSConfig
from app.ats.registry import ATSProviderRegistry
from app.browser.service import BrowserService

logger = structlog.get_logger(__name__)


class ATSProviderFactory:
    def __init__(
        self,
        registry: ATSProviderRegistry,
        config: ATSConfig,
        browser: BrowserService,
    ) -> None:
        self._registry = registry
        self._config = config
        self._browser = browser

    def register_all(self) -> None:
        from app.ats.providers.ashby import AshbyATSProvider
        from app.ats.providers.bamboohr import BambooHRATSProvider
        from app.ats.providers.greenhouse import GreenhouseATSProvider
        from app.ats.providers.lever import LeverATSProvider
        from app.ats.providers.recruitee import RecruiteeATSProvider
        from app.ats.providers.smartrecruiters import SmartRecruitersATSProvider
        from app.ats.providers.workday import WorkdayATSProvider

        registrations: list[tuple[str, type]] = [
            ("greenhouse", GreenhouseATSProvider),
            ("lever", LeverATSProvider),
            ("ashby", AshbyATSProvider),
            ("workday", WorkdayATSProvider),
            ("smartrecruiters", SmartRecruitersATSProvider),
            ("bamboohr", BambooHRATSProvider),
            ("recruitee", RecruiteeATSProvider),
        ]

        for name, provider_class in registrations:
            if not self._registry.is_registered(name):
                provider_config = getattr(self._config, name, None)
                provider = provider_class(browser=self._browser, config=provider_config)
                self._registry.register(provider)
                logger.info("Registered ATS provider", name=name)

    def create_provider(self, name: str) -> Any:
        from app.ats.providers.ashby import AshbyATSProvider
        from app.ats.providers.bamboohr import BambooHRATSProvider
        from app.ats.providers.greenhouse import GreenhouseATSProvider
        from app.ats.providers.lever import LeverATSProvider
        from app.ats.providers.recruitee import RecruiteeATSProvider
        from app.ats.providers.smartrecruiters import SmartRecruitersATSProvider
        from app.ats.providers.workday import WorkdayATSProvider

        mapping: dict[str, type] = {
            "greenhouse": GreenhouseATSProvider,
            "lever": LeverATSProvider,
            "ashby": AshbyATSProvider,
            "workday": WorkdayATSProvider,
            "smartrecruiters": SmartRecruitersATSProvider,
            "bamboohr": BambooHRATSProvider,
            "recruitee": RecruiteeATSProvider,
        }

        provider_class = mapping.get(name)
        if provider_class is None:
            raise ValueError(f"Unknown ATS provider: {name}")

        provider_config = getattr(self._config, name, None)
        return provider_class(browser=self._browser, config=provider_config)

    def detect_provider(self, url: str) -> Any | None:
        return self._registry.detect(url)
