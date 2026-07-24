from __future__ import annotations

from app.application_package.cache import PackageCache
from app.application_package.config import PackageConfig
from app.application_package.generator import PackageGenerator
from app.application_package.schemas import ApplicationPackage


class ApplicationPackageService:
    def __init__(
        self,
        config: PackageConfig | None = None,
    ) -> None:
        self._config = config or PackageConfig()
        self._generator = PackageGenerator(self._config)
        self._cache = PackageCache(self._config)

    def generate(
        self,
        job_posting=None,
        profile_intelligence=None,
        application_intelligence=None,
        match_result=None,
        optimized_resume=None,
        generated_cover_letter=None,
        skip_cache: bool = False,
    ) -> ApplicationPackage:
        profile_hash = getattr(profile_intelligence, "profile_hash", None) if profile_intelligence else None
        job_hash = self._generator.compute_job_hash(job_posting) if job_posting else None
        resume_hash = getattr(optimized_resume, "resume_hash", None) if optimized_resume else None
        cover_letter_hash = getattr(generated_cover_letter, "id", None) if generated_cover_letter else None
        match_hash = getattr(match_result, "id", None) if match_result else None

        if not skip_cache:
            cache_key = PackageCache.compute_key(profile_hash, job_hash, resume_hash, cover_letter_hash, match_hash)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        package = self._generator.generate(
            job=job_posting,
            profile=profile_intelligence,
            application_intelligence=application_intelligence,
            match_result=match_result,
            resume=optimized_resume,
            cover_letter=generated_cover_letter,
        )

        if not skip_cache:
            self._cache.set(cache_key, package)

        return package

    def invalidate_cache(
        self,
        profile_hash: str | None = None,
        job_hash: str | None = None,
        resume_hash: str | None = None,
        cover_letter_hash: str | None = None,
        match_hash: str | None = None,
    ) -> None:
        cache_key = PackageCache.compute_key(profile_hash, job_hash, resume_hash, cover_letter_hash, match_hash)
        self._cache.invalidate(cache_key)

    def clear_cache(self) -> None:
        self._cache.clear()
