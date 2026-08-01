import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NoResumeAvailableError, NotFoundError
from app.models import Application, CoverLetter, Job, ResumeVersion, UserAISettings
from app.repositories import (
    ApplicationRepository,
    CareerProfileRepository,
    CoverLetterRepository,
    JobRepository,
    ResumeVersionRepository,
    UserAISettingsRepository,
)
from app.schemas.resume_strategy import (
    RESUME_STRATEGY_ASK,
    RESUME_STRATEGY_GENERATE,
    RESUME_STRATEGY_TAILOR,
    RESUME_STRATEGY_USE_EXISTING,
    SAVE_GENERATED_EVERY,
    SAVE_GENERATED_SUBMITTED_ONLY,
)
from app.services.ai_settings import AISettingsService
from app.services.audit import AuditService
from app.services.resume import ResumeService

logger = logging.getLogger(__name__)


class ResumeStrategyService:
    """Coordinates resume selection, tailoring, generation, and storage for every application."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.resume_repo = ResumeVersionRepository(session)
        self.job_repo = JobRepository(session)
        self.app_repo = ApplicationRepository(session)
        self.profile_repo = CareerProfileRepository(session)
        self.cover_letter_repo = CoverLetterRepository(session)
        self.settings_repo = UserAISettingsRepository(session)
        self.audit_service = AuditService(session)
        self.resume_service = ResumeService(session)
        self.ai_settings_service = AISettingsService(session)

    # ── Settings ──

    async def get_settings(self, user_id: uuid.UUID) -> UserAISettings:
        return await self.ai_settings_service.get_settings(user_id)

    async def update_settings(
        self,
        user_id: uuid.UUID,
        resume_strategy: str | None = None,
        save_generated_resumes: str | None = None,
    ) -> UserAISettings:
        return await self.ai_settings_service.update_settings(
            user_id,
            resume_strategy=resume_strategy,
            save_generated_resumes=save_generated_resumes,
        )

    async def resolve_strategy(self, user_id: uuid.UUID, override: str | None = None) -> str:
        if override:
            return override
        settings = await self.get_settings(user_id)
        return settings.resume_strategy

    # ── Resume selection ──

    async def select_resume(self, user_id: uuid.UUID, job: Job) -> dict:
        """Choose the best master resume for a job using deterministic scoring.

        Never falls back to "newest upload": candidates are ranked by skill
        overlap, keyword overlap, role alignment, and ATS compatibility.
        """
        masters = await self.resume_repo.list_master_resumes_with_sections(user_id)
        job_skills = self._extract_job_skills(job)
        job_tokens = self._tokenize(f"{job.title} {job.description or ''}")
        scores = []
        for resume in masters:
            text = self._resume_text(resume)
            resume_tokens = self._tokenize(text)
            resume_skills = self._extract_resume_skills(text)
            scores.append(
                self._score_candidate(
                    resume, text, job, job_skills, job_tokens, resume_tokens, resume_skills
                )
            )

        if not scores:
            return {
                "job_id": job.id,
                "selected_resume_id": None,
                "selected_title": None,
                "scores": [],
                "rationale": "No master resumes available.",
            }

        best = max(scores, key=lambda s: (s["overall"], s["resume"].is_default))
        best["selected"] = True
        return {
            "job_id": job.id,
            "selected_resume_id": best["resume"].id,
            "selected_title": best["resume"].title,
            "scores": [
                {
                    "resume_id": s["resume"].id,
                    "title": s["resume"].title,
                    "skill_overlap": round(s["skill_overlap"], 4),
                    "keyword_overlap": round(s["keyword_overlap"], 4),
                    "role_alignment": round(s["role_alignment"], 4),
                    "ats_compatibility": round(s["ats_compatibility"], 4),
                    "overall": round(s["overall"], 4),
                    "selected": s["selected"],
                }
                for s in scores
            ],
            "rationale": f"Selected '{best['resume'].title}' with the highest overall fit score.",
        }

    def _score_candidate(
        self,
        resume: ResumeVersion,
        text: str,
        job: Job,
        job_skills: set[str],
        job_tokens: set[str],
        resume_tokens: set[str],
        resume_skills: set[str],
    ) -> dict:
        skill_overlap = len(job_skills & resume_skills) / len(job_skills) if job_skills else 0.0
        keyword_overlap = (
            len(job_tokens & resume_tokens) / len(job_tokens) if job_tokens else 0.0
        )
        title_tokens = set(self._tokenize(job.title or ""))
        role_alignment = (
            len(title_tokens & resume_tokens) / len(title_tokens) if title_tokens else 0.0
        )
        ats = self._ats_compatibility(resume, text)
        overall = skill_overlap * 0.45 + keyword_overlap * 0.25 + role_alignment * 0.20 + ats * 0.10
        return {
            "resume": resume,
            "skill_overlap": skill_overlap,
            "keyword_overlap": keyword_overlap,
            "role_alignment": role_alignment,
            "ats_compatibility": ats,
            "overall": overall,
            "selected": False,
        }

    @staticmethod
    def _ats_compatibility(resume: ResumeVersion, text: str) -> float:
        sections = resume.sections or []
        types = {s.section_type for s in sections}
        has_summary = "summary" in types
        has_experience = "experience" in types
        has_education = "education" in types
        has_skills = "skills" in types
        score = 0.25
        if has_summary:
            score += 0.20
        if has_experience:
            score += 0.25
        if has_education:
            score += 0.15
        if has_skills:
            score += 0.15
        return score

    # ── Text/keyword helpers ──

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {t for t in re.findall(r"[a-z0-9+#.-]+", (text or "").lower()) if len(t) > 1}

    def _extract_job_skills(self, job: Job) -> set[str]:
        desc = (job.description or "").lower()
        return {s for s in ResumeService.KNOWN_TECH_KEYWORDS if s in desc}

    def _extract_resume_skills(self, text: str) -> set[str]:
        lower = text.lower()
        return {s for s in ResumeService.KNOWN_TECH_KEYWORDS if s in lower}

    @staticmethod
    def _resume_text(resume: ResumeVersion) -> str:
        texts = []
        for section in resume.sections or []:
            content = section.content
            if isinstance(content, dict):
                text = content.get("text", "") or ""
                bullets = content.get("bullet_points") or content.get("bullets")
                if isinstance(bullets, list):
                    text = "\n".join([text, *[str(b) for b in bullets]])
            elif isinstance(content, str):
                text = content
            else:
                text = ""
            if text.strip():
                texts.append(text)
        return "\n".join(texts)

    @staticmethod
    def _build_resume_name(job: Job, version: int) -> str:
        company = re.sub(r"[^a-zA-Z0-9]+", "_", (job.company or "Company")).strip("_")
        role = re.sub(r"[^a-zA-Z0-9]+", "_", (job.title or "Role")).strip("_")
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{company}_{role}_{date}_v{version}"

    async def _profile_fingerprint(self, user_id: uuid.UUID) -> str:
        profile = await self.profile_repo.get_by_user(user_id)
        if not profile:
            return "no-profile"
        return f"{profile.updated_at.isoformat() if profile.updated_at else 'never'}"

    @staticmethod
    def _job_fingerprint(job: Job) -> str:
        return hashlib.sha256((job.description or "").encode("utf-8")).hexdigest()

    # ── Generation / tailoring ──

    async def _reusable_generated(
        self,
        user_id: uuid.UUID,
        job: Job,
        mode: str,
    ) -> ResumeVersion | None:
        existing = await self.resume_repo.get_generated_for_job(user_id, job.id)
        if not existing:
            return None
        meta = existing.generation_metadata or {}
        profile_ok = meta.get("profile_fingerprint") == await self._profile_fingerprint(user_id)
        job_ok = meta.get("job_fingerprint") == self._job_fingerprint(job)
        mode_ok = meta.get("mode") == mode
        if profile_ok and job_ok and mode_ok:
            return existing
        return None

    async def _tailor_resume(
        self,
        user_id: uuid.UUID,
        job: Job,
        source_resume: ResumeVersion,
        target_role: str | None,
    ) -> tuple[ResumeVersion, bool]:
        """Tailor the best master resume to the job. Reuses a previous tailoring when inputs are unchanged."""
        cached = await self._reusable_generated(user_id, job, mode="tailor")
        if cached is not None:
            return cached, True

        latest_version = await self.resume_repo.latest_version(user_id)
        new_resume = await self.resume_service.optimize_for_job(
            resume_id=source_resume.id,
            user_id=user_id,
            job_id=job.id,
            target_role=target_role or job.title,
            enhance_with_ai=True,
        )
        new_resume.title = self._build_resume_name(job, latest_version + 1)
        new_resume.resume_type = "tailored"
        new_resume.origin = "generated"
        new_resume.parent_resume_id = source_resume.id
        new_resume.generation_metadata = {
            "mode": "tailor",
            "source_resume_id": str(source_resume.id),
            "job_fingerprint": self._job_fingerprint(job),
            "profile_fingerprint": await self._profile_fingerprint(user_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "change_summary": "AI tailored to job: summary, skills, experience, projects, ATS keywords",
        }
        await self.resume_repo.update(new_resume)
        await self.audit_service.log(
            "RESUME_TAILORED",
            user_id=user_id,
            entity="resume",
            entity_id=new_resume.id,
            outcome="success",
            details={"job_id": str(job.id), "source_resume_id": str(source_resume.id)},
        )
        return new_resume, False

    async def _generate_resume(
        self,
        user_id: uuid.UUID,
        job: Job,
    ) -> tuple[ResumeVersion, bool]:
        """Generate a fresh resume from the career profile. Reuses a previous generation when inputs are unchanged."""
        cached = await self._reusable_generated(user_id, job, mode="generate")
        if cached is not None:
            return cached, True

        latest_version = await self.resume_repo.latest_version(user_id)
        generated = await self.resume_service.generate_from_profile(
            user_id=user_id,
            title=self._build_resume_name(job, latest_version + 1),
            enhance_with_ai=True,
        )
        generated.origin = "generated"
        generated.resume_type = "generated"
        generated.generated_for_job_id = job.id
        generated.generation_metadata = {
            "mode": "generate",
            "job_fingerprint": self._job_fingerprint(job),
            "profile_fingerprint": await self._profile_fingerprint(user_id),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "change_summary": "Generated from career profile and optimized for job",
        }
        await self.resume_repo.update(generated)
        await self.audit_service.log(
            "RESUME_GENERATED_FOR_JOB",
            user_id=user_id,
            entity="resume",
            entity_id=generated.id,
            outcome="success",
            details={"job_id": str(job.id)},
        )
        return generated, False

    async def _generate_cover_letter(
        self,
        user_id: uuid.UUID,
        job: Job,
        resume: ResumeVersion,
    ) -> CoverLetter | None:
        try:
            from app.ai.features.cover_letter import ai_generate_cover_letter

            result = await ai_generate_cover_letter(
                job_title=job.title,
                company_name=job.company,
                job_description=job.description or "",
                resume_text=self._resume_text(resume),
            )
            content = result.get("cover_letter") or ""
            if not content.strip():
                return None
            cover_letter = CoverLetter(
                user_id=user_id,
                job_id=job.id,
                resume_id=resume.id,
                title=f"Cover Letter - {job.company} - {job.title}",
                company_name=job.company,
                job_title=job.title,
                content=content,
                status="active",
            )
            created = await self.cover_letter_repo.create(cover_letter)
            return created
        except Exception:
            logger.exception("Cover letter generation failed; continuing without it.")
            return None

    # ── Preview ──

    async def preview(self, user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
        """Score master resumes against a job and recommend a strategy without persisting anything."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found.")

        selection = await self.select_resume(user_id, job)
        best = selection["scores"][0] if selection["scores"] else None

        if best is None:
            recommended = RESUME_STRATEGY_GENERATE
            rationale = "No master resumes available. Generate a resume from your career profile."
        elif best["overall"] >= 0.6:
            recommended = RESUME_STRATEGY_USE_EXISTING
            rationale = f"'{best['title']}' already fits this job well; reuse it to save AI credits."
        elif best["overall"] >= 0.35:
            recommended = RESUME_STRATEGY_TAILOR
            rationale = f"'{best['title']}' is a solid base; tailor it to this job for a stronger match."
        else:
            recommended = RESUME_STRATEGY_GENERATE
            rationale = "No master resume fits this job well; generate a new one from your career profile."

        generated = await self._reusable_generated(user_id, job, mode="tailor") or await self._reusable_generated(
            user_id, job, mode="generate"
        )
        return {
            "recommended_strategy": recommended,
            "selected_resume_id": selection["selected_resume_id"],
            "selected_resume_title": selection["selected_title"],
            "scores": selection["scores"],
            "generated_resume_id": generated.id if generated else None,
            "generated_resume_title": generated.title if generated else None,
            "reused_generated": generated is not None,
            "rationale": rationale,
        }

    # ── Application preparation ──

    async def prepare_application(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        strategy_override: str | None = None,
        resume_id: uuid.UUID | None = None,
        generate_cover_letter: bool = True,
    ) -> dict:
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found.")

        strategy = await self.resolve_strategy(user_id, strategy_override)

        if strategy == RESUME_STRATEGY_ASK:
            selection = await self.select_resume(user_id, job)
            return {
                "needs_choice": True,
                "strategy": strategy,
                "job_id": job.id,
                "selected_resume_id": selection["selected_resume_id"],
                "selected_resume_title": selection["selected_title"],
                "options": [
                    RESUME_STRATEGY_USE_EXISTING,
                    RESUME_STRATEGY_TAILOR,
                    RESUME_STRATEGY_GENERATE,
                ],
            }

        selected = None
        if resume_id is not None:
            selected = await self.resume_repo.get_with_sections(resume_id)
            if not selected or selected.user_id != user_id or selected.origin != "master":
                raise NotFoundError("Resume not found.")
        else:
            selection = await self.select_resume(user_id, job)
            if selection["selected_resume_id"]:
                selected = await self.resume_repo.get_with_sections(selection["selected_resume_id"])

        resume = None
        generated_resume = None
        reused = False
        generated_flag = False
        tailored_flag = False

        if strategy == RESUME_STRATEGY_USE_EXISTING:
            if selected is None:
                raise NoResumeAvailableError(
                    "You do not have a resume yet. Upload a resume or generate one from your career profile.",
                    details={"options": ["upload", "generate"]},
                )
            resume = selected
        elif strategy == RESUME_STRATEGY_TAILOR:
            if selected is None:
                raise NoResumeAvailableError(
                    "You do not have a resume yet. Generate one from your career profile or upload one.",
                    details={"options": ["generate", "upload"]},
                )
            generated_resume, reused = await self._tailor_resume(user_id, job, selected, job.title)
            resume = generated_resume
            generated_flag = True
            tailored_flag = True
        elif strategy == RESUME_STRATEGY_GENERATE:
            generated_resume, reused = await self._generate_resume(user_id, job)
            resume = generated_resume
            generated_flag = True

        cover_letter = None
        if generate_cover_letter:
            cover_letter = await self._generate_cover_letter(user_id, job, resume)

        existing = await self.app_repo.exists(user_id, job_id)
        if existing and not reused:
            from app.core.exceptions import ConflictError

            raise ConflictError("Application already exists for this job.")

        if existing and reused:
            return {
                "needs_choice": False,
                "strategy": strategy,
                "application_id": None,
                "status": None,
                "selected_resume_id": selected.id if selected else None,
                "selected_resume_title": selected.title if selected else None,
                "generated_resume_id": generated_resume.id if generated_resume else None,
                "generated_resume_title": generated_resume.title if generated_resume else None,
                "cover_letter_id": None,
                "reused_generated": True,
                "reason": "A generated resume already exists for this job with unchanged inputs.",
                "created_at": None,
            }

        application = Application(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume.id,
            cover_letter_id=cover_letter.id if cover_letter else None,
            resume_strategy=strategy,
            original_resume_id=selected.id if selected else None,
            generated_resume_id=generated_resume.id if generated_resume else None,
            generated=generated_flag,
            tailored=tailored_flag,
            generation_timestamp=datetime.now(timezone.utc),
            status="Ready for Review",
        )
        created = await self.app_repo.create(application)
        await self.audit_service.log(
            "APPLICATION_PREPARED",
            user_id=user_id,
            entity="application",
            entity_id=created.id,
            outcome="success",
            details={"strategy": strategy, "reused_generated": reused},
        )
        return {
            "needs_choice": False,
            "strategy": strategy,
            "application_id": created.id,
            "status": created.status,
            "selected_resume_id": selected.id if selected else None,
            "selected_resume_title": selected.title if selected else None,
            "generated_resume_id": generated_resume.id if generated_resume else None,
            "generated_resume_title": generated_resume.title if generated_resume else None,
            "cover_letter_id": cover_letter.id if cover_letter else None,
            "reused_generated": reused,
            "created_at": created.created_at,
        }

    # ── Storage policy (save generated resumes) ──

    async def finalize_application(self, application: Application, submitted: bool) -> None:
        """Apply the save-generated-resumes policy once an application terminates.

        - every: keep every generated resume.
        - submitted_only (default): keep the generated resume only when the
          application was submitted; delete it otherwise.
        - never: never persist generated resumes.
        """
        if not application.generated_resume_id:
            return
        settings = await self.ai_settings_service.get_settings(application.user_id)
        option = settings.save_generated_resumes
        if option == SAVE_GENERATED_EVERY:
            return
        if option == SAVE_GENERATED_SUBMITTED_ONLY and submitted:
            return

        generated = await self.resume_repo.get_by_id(application.generated_resume_id)
        if generated:
            await self.resume_repo.delete(generated)
        application.generated_resume_id = None
        if application.resume_id is None or application.resume_id == generated.id:
            application.resume_id = application.original_resume_id
        application.generated = False
        await self.app_repo.update(application)
        await self.audit_service.log(
            "GENERATED_RESUME_DISCARDED",
            user_id=application.user_id,
            entity="application",
            entity_id=application.id,
            outcome="success",
            details={"save_generated_resumes": option, "submitted": submitted},
        )

    async def list_generated_resumes(self, user_id: uuid.UUID) -> list[ResumeVersion]:
        return await self.resume_repo.list_by_user_and_origin(user_id, "generated")

    async def list_master_resumes(self, user_id: uuid.UUID) -> list[ResumeVersion]:
        return await self.resume_repo.list_by_user_and_origin(user_id, "master")
