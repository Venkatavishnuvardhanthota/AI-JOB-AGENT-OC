from __future__ import annotations

from app.resume_optimization.ats import ATSScorer
from app.resume_optimization.cache import OptimizationCache
from app.resume_optimization.config import OptimizationConfig
from app.resume_optimization.keyword_extractor import KeywordExtractor
from app.resume_optimization.optimizer import ResumeOptimizer
from app.resume_optimization.schemas import OptimizedResume
from app.resume_optimization.section_optimizer import SectionOptimizer
from app.resume_optimization.validator import ResumeValidator


class ResumeOptimizationService:
    def __init__(
        self,
        config: OptimizationConfig | None = None,
    ) -> None:
        self._config = config or OptimizationConfig()
        self._keyword_extractor = KeywordExtractor()
        self._section_optimizer = SectionOptimizer(self._keyword_extractor)
        self._ats_scorer = ATSScorer()
        self._optimizer = ResumeOptimizer(
            self._config, self._keyword_extractor, self._section_optimizer, self._ats_scorer,
        )
        self._validator = ResumeValidator(self._config)
        self._cache = OptimizationCache(self._config)

    def optimize(
        self,
        resume,
        job_posting,
        profile,
        match_result,
        *,
        skip_cache: bool = False,
    ) -> OptimizedResume:
        self._validator.assert_valid_input(resume, job_posting, profile)

        cache_key = self._cache.compute_key(
            getattr(profile, "profile_hash", None) if profile else None,
            getattr(self, "_compute_job_hash", lambda j: None)(job_posting),
        )

        if not skip_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        result = self._optimizer.optimize(resume, job_posting, profile, match_result)
        self._cache.set(cache_key, result)
        return result

    def invalidate_cache(self, key: str) -> None:
        self._cache.invalidate(key)

    def clear_cache(self) -> None:
        self._cache.clear()
