from __future__ import annotations

from app.cover_letter.cache import CoverLetterCache
from app.cover_letter.config import CoverLetterConfig
from app.cover_letter.generator import CoverLetterGenerator
from app.cover_letter.personalizer import Personalizer
from app.cover_letter.schemas import GeneratedCoverLetter
from app.cover_letter.templates import TemplateEngine
from app.cover_letter.validator import CoverLetterValidator


class CoverLetterGenerationService:
    def __init__(
        self,
        config: CoverLetterConfig | None = None,
    ) -> None:
        self._config = config or CoverLetterConfig()
        self._template_engine = TemplateEngine()
        self._personalizer = Personalizer()
        self._validator = CoverLetterValidator(self._config)
        self._generator = CoverLetterGenerator(
            self._config, self._template_engine, self._personalizer, self._validator,
        )
        self._cache = CoverLetterCache(self._config)

    def generate(
        self,
        profile,
        job_posting,
        optimized_resume,
        match_result,
        *,
        skip_cache: bool = False,
        tone: str | None = None,
        length: str | None = None,
        template_style: str | None = None,
    ) -> GeneratedCoverLetter:
        effective_config = self._config
        if tone or length or template_style:
            effective_config = CoverLetterConfig(
                tone=tone or self._config.tone,
                length=length or self._config.length,
                template_style=template_style or self._config.template_style,
                cache_ttl_seconds=self._config.cache_ttl_seconds,
                strict_validation=self._config.strict_validation,
            )

        self._validator.assert_valid_inputs(profile, job_posting, optimized_resume)

        profile_hash = getattr(profile, "profile_hash", None) if profile else None
        resume_hash = getattr(optimized_resume, "resume_hash", None) if optimized_resume else None
        job_hash = self._compute_job_hash(job_posting)

        cache_key = self._cache.compute_key(
            profile_hash, job_hash, resume_hash,
            effective_config.template_style, effective_config.tone,
        )

        if not skip_cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        generator = CoverLetterGenerator(
            effective_config, self._template_engine, self._personalizer, self._validator,
        )
        result = generator.generate(profile, job_posting, optimized_resume, match_result)
        result.profile_hash = profile_hash
        result.job_hash = job_hash
        result.resume_hash = resume_hash
        self._cache.set(cache_key, result)
        return result

    def invalidate_cache(self, key: str) -> None:
        self._cache.invalidate(key)

    def clear_cache(self) -> None:
        self._cache.clear()

    def list_templates(self) -> list[str]:
        return self._template_engine.list_styles()

    @staticmethod
    def _compute_job_hash(job) -> str | None:
        if not job:
            return None
        import hashlib
        import json
        data = {
            "title": getattr(job, "title", None),
            "skills": getattr(job, "skills", None),
        }
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
