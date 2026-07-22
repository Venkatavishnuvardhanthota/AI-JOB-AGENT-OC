from __future__ import annotations

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.registry import JobProviderRegistry

logger = structlog.get_logger(__name__)


class JobProviderFactory:
    def __init__(self, registry: JobProviderRegistry, config: JobDiscoveryConfig) -> None:
        self._registry = registry
        self._config = config

    def register_all(self) -> None:
        from app.jobs.providers.adzuna import AdzunaJobProvider
        from app.jobs.providers.ashby import AshbyJobProvider
        from app.jobs.providers.bamboohr import BambooHRJobProvider
        from app.jobs.providers.foundit import FounditJobProvider
        from app.jobs.providers.freshersworld import FreshersworldJobProvider
        from app.jobs.providers.greenhouse import GreenhouseJobProvider
        from app.jobs.providers.internshala import InternshalaJobProvider
        from app.jobs.providers.lever import LeverJobProvider
        from app.jobs.providers.mock import MockJobProvider
        from app.jobs.providers.naukri import NaukriJobProvider
        from app.jobs.providers.recruitee import RecruiteeJobProvider
        from app.jobs.providers.smartrecruiters import SmartRecruitersJobProvider
        from app.jobs.providers.unstop import UnstopJobProvider
        from app.jobs.providers.wellfound import WellfoundJobProvider
        from app.jobs.providers.workday import WorkdayJobProvider
        from app.jobs.providers.y_combinator import YCombinatorJobProvider

        registrations: list[tuple[str, type]] = [
            ("mock", MockJobProvider),
        ]

        enabled = self._config.enabled_providers
        if "adzuna" in enabled and self._config.adzuna.app_id and self._config.adzuna.api_key:
            registrations.append(("adzuna", AdzunaJobProvider))

        if "wellfound" in enabled:
            registrations.append(("wellfound", WellfoundJobProvider))

        if "y_combinator" in enabled:
            registrations.append(("y_combinator", YCombinatorJobProvider))

        if "greenhouse" in enabled:
            registrations.append(("greenhouse", GreenhouseJobProvider))

        if "lever" in enabled:
            registrations.append(("lever", LeverJobProvider))

        if "ashby" in enabled:
            registrations.append(("ashby", AshbyJobProvider))

        if "naukri" in enabled:
            registrations.append(("naukri", NaukriJobProvider))

        if "foundit" in enabled:
            registrations.append(("foundit", FounditJobProvider))

        if "internshala" in enabled:
            registrations.append(("internshala", InternshalaJobProvider))

        if "freshersworld" in enabled:
            registrations.append(("freshersworld", FreshersworldJobProvider))

        if "unstop" in enabled:
            registrations.append(("unstop", UnstopJobProvider))

        if "workday" in enabled:
            registrations.append(("workday", WorkdayJobProvider))

        if "smartrecruiters" in enabled:
            registrations.append(("smartrecruiters", SmartRecruitersJobProvider))

        if "bamboohr" in enabled:
            registrations.append(("bamboohr", BambooHRJobProvider))

        if "recruitee" in enabled:
            registrations.append(("recruitee", RecruiteeJobProvider))

        for name, provider_class in registrations:
            if not self._registry.is_registered(name):
                provider = provider_class(self._config)
                self._registry.register(provider)
                logger.info("Registered job provider", name=name)
