from __future__ import annotations

from app.application_intelligence.analyzer import ApplicationIntelligenceAnalyzer
from app.application_intelligence.config import ApplicationIntelligenceConfig
from app.application_intelligence.schemas import ApplicationIntelligence


class ApplicationIntelligenceService:
    def __init__(
        self,
        config: ApplicationIntelligenceConfig | None = None,
    ) -> None:
        self._config = config or ApplicationIntelligenceConfig()
        self._analyzer = ApplicationIntelligenceAnalyzer(self._config)

    def analyze(
        self,
        job,
        match_result=None,
        profile_intelligence=None,
        skip_cache: bool = False,
    ) -> ApplicationIntelligence:
        return self._analyzer.analyze(
            job=job,
            match_result=match_result,
            profile_intelligence=profile_intelligence,
            skip_cache=skip_cache,
        )

    def invalidate_cache(self, key: str) -> None:
        self._analyzer.invalidate_cache(key)

    def clear_cache(self) -> None:
        self._analyzer.clear_cache()
