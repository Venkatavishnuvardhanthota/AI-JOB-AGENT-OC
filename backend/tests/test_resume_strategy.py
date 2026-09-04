import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NoResumeAvailableError, NotFoundError, ValidationError
from app.schemas.resume_strategy import (
    RESUME_STRATEGY_ASK,
    RESUME_STRATEGY_GENERATE,
    RESUME_STRATEGY_TAILOR,
    RESUME_STRATEGY_USE_EXISTING,
    SAVE_GENERATED_EVERY,
    SAVE_GENERATED_NEVER,
    SAVE_GENERATED_SUBMITTED_ONLY,
)
from app.services.resume_strategy import ResumeStrategyService
from database.models.application import Application
from database.models.career_profile import CareerProfile
from database.models.job import Job
from database.models.resume_section import ResumeSection
from database.models.resume_version import ResumeVersion
from database.models.user import User
from database.models.user_ai_settings import UserAISettings
from database.repositories import JobRepository, ResumeVersionRepository, UserAISettingsRepository, UserRepository


async def _create_user(session: AsyncSession, email: str = "strategy@test.com") -> User:
    return await UserRepository(session).create(
        User(email=email, password_hash="h", first_name="Strategy", last_name="Test")
    )


async def _create_job(
    session: AsyncSession,
    title: str = "Python Developer",
    description: str = "Build APIs with python, fastapi, sqlalchemy, docker and postgresql.",
) -> Job:
    return await JobRepository(session).create(
        Job(provider="manual", title=title, company="Acme Corp", description=description)
    )


async def _create_master_resume(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    version: int = 1,
    title: str = "Master Resume",
    text: str = "Senior Python developer skilled in python, fastapi, sqlalchemy.",
) -> ResumeVersion:
    resume = ResumeVersion(user_id=user_id, version=version, title=title, status="draft", source="manual")
    session.add(resume)
    await session.flush()
    session.add(
        ResumeSection(
            resume_id=resume.id,
            section_type="summary",
            title="Summary",
            content={"text": text},
            sort_order=0,
            visible=True,
        )
    )
    await session.flush()
    return resume


@pytest_asyncio.fixture
async def mock_ai(monkeypatch):
    async def _improve(section_type="", current_content="", target_role="", job_context="", improvement_areas=""):
        return {"improved_content": f"IMPROVED {section_type}: {current_content}"}

    async def _cover_letter(
        job_title="",
        company_name="",
        job_description="",
        resume_text="",
        tone="professional",
        style="modern",
        hiring_manager="",
    ):
        return {"cover_letter": f"Cover letter for {job_title} at {company_name}"}

    monkeypatch.setattr("app.ai.features.resume.ai_improve_resume_section", _improve)
    monkeypatch.setattr("app.ai.features.cover_letter.ai_generate_cover_letter", _cover_letter)
    return {"improve": _improve, "cover_letter": _cover_letter}


# ── Unit Tests (no database) ──


class TestTextHelpers:
    def test_tokenize_normalizes(self):
        service = ResumeStrategyService.__new__(ResumeStrategyService)
        assert service._tokenize("Python, FastAPI & Docker!") == {"python", "fastapi", "docker"}

    def test_tokenize_skips_single_chars(self):
        service = ResumeStrategyService.__new__(ResumeStrategyService)
        assert "a" not in service._tokenize("a b c python")

    def test_resume_text_extracts_dict_and_bullets(self):
        resume = ResumeVersion()
        resume.sections = [
            ResumeSection(section_type="summary", content={"text": "Headline"}),
            ResumeSection(section_type="experience", content={"text": "Role", "bullet_points": ["b1", "b2"]}),
            ResumeSection(section_type="skills", content={"text": ""}),
        ]
        service = ResumeStrategyService.__new__(ResumeStrategyService)
        text = service._resume_text(resume)
        assert "Headline" in text
        assert "Role" in text
        assert "b1" in text
        assert "b2" in text

    def test_job_skill_extraction_uses_known_keywords(self):
        job = Job(provider="manual", title="Backend Engineer", company="X", description="We love python and docker")
        service = ResumeStrategyService.__new__(ResumeStrategyService)
        skills = service._extract_job_skills(job)
        assert "python" in skills
        assert "docker" in skills
        assert "fastapi" not in skills

    def test_resume_skill_extraction(self):
        service = ResumeStrategyService.__new__(ResumeStrategyService)
        skills = service._extract_resume_skills("expert in python, postgresql and kubernetes")
        assert {"python", "postgresql", "kubernetes"}.issubset(skills)

    def test_build_resume_name(self):
        job = Job(provider="manual", title="Python Developer!", company="Acme Corp", description="x")
        name = ResumeStrategyService._build_resume_name(job, 7)
        assert name.startswith("Acme_Corp_Python_Developer")
        assert "_v7" in name
        assert "!" not in name

    def test_job_fingerprint_is_deterministic(self):
        job1 = Job(provider="manual", title="T", company="C", description="same description")
        job2 = Job(provider="manual", title="T", company="C", description="same description")
        assert ResumeStrategyService._job_fingerprint(job1) == ResumeStrategyService._job_fingerprint(job2)
        job2.description = "different"
        assert ResumeStrategyService._job_fingerprint(job1) != ResumeStrategyService._job_fingerprint(job2)

    def test_ats_compatibility_scores_sections(self):
        service = ResumeStrategyService.__new__(ResumeStrategyService)
        partial = ResumeVersion()
        partial.sections = [ResumeSection(section_type="summary", content={"text": "x"})]
        full = ResumeVersion()
        full.sections = [
            ResumeSection(section_type="summary", content={"text": "x"}),
            ResumeSection(section_type="experience", content={"text": "x"}),
            ResumeSection(section_type="education", content={"text": "x"}),
            ResumeSection(section_type="skills", content={"text": "x"}),
        ]
        assert service._ats_compatibility(partial, "x") == 0.45
        assert service._ats_compatibility(full, "x") == 1.0


class TestSelectionScoring:
    @pytest.mark.asyncio
    async def test_selects_resume_with_best_skill_overlap(self):
        session = AsyncSession.__new__(AsyncSession)
        service = ResumeStrategyService(session)
        job = Job(
            provider="manual", title="Python Developer", company="X", description="python docker fastapi postgresql"
        )

        good = ResumeVersion(title="Good", version=1)
        good.sections = [
            ResumeSection(
                section_type="skills", content={"text": "python, docker, fastapi, postgresql, sqlalchemy"}
            )
        ]
        bad = ResumeVersion(title="Bad", version=2)
        bad.sections = [ResumeSection(section_type="skills", content={"text": "excel, word"})]

        service.resume_repo = type("Repo", (), {"list_master_resumes_with_sections": _async_return([good, bad])})()
        service.job_repo = type("Repo", (), {"get_by_id": _async_return(job)})()
        result = await service.select_resume(uuid.uuid4(), job)
        assert result["selected_resume_id"] == good.id
        scores = {s["title"]: s for s in result["scores"]}
        assert scores["Good"]["overall"] > scores["Bad"]["overall"]
        assert scores["Good"]["selected"] is True

    @pytest.mark.asyncio
    async def test_select_resume_no_masters(self):
        job = Job(provider="manual", title="T", company="C", description="x")
        service = ResumeStrategyService(AsyncSession.__new__(AsyncSession))
        service.resume_repo = type("Repo", (), {"list_master_resumes_with_sections": _async_return([])})()
        result = await service.select_resume(uuid.uuid4(), job)
        assert result["selected_resume_id"] is None
        assert result["scores"] == []

    @pytest.mark.asyncio
    async def test_recommendation_thresholds(self):
        job = Job(
            provider="manual",
            title="Python Developer",
            company="X",
            description="python docker fastapi postgresql sqlalchemy",
        )
        service = ResumeStrategyService(AsyncSession.__new__(AsyncSession))
        service.resume_repo = type("Repo", (), {"list_master_resumes_with_sections": _async_return([])})()
        service.job_repo = type("Repo", (), {"get_by_id": _async_return(job)})()
        service._reusable_generated = _async_return(None)
        preview = await service.preview(uuid.uuid4(), uuid.uuid4())
        assert preview["recommended_strategy"] == RESUME_STRATEGY_GENERATE

    @pytest.mark.asyncio
    async def test_preview_no_job_raises(self):
        service = ResumeStrategyService(AsyncSession.__new__(AsyncSession))
        service.job_repo = type("Repo", (), {"get_by_id": _async_return(None)})()
        with pytest.raises(NotFoundError):
            await service.preview(uuid.uuid4(), uuid.uuid4())


class TestStrategyResolution:
    @pytest.mark.asyncio
    async def test_override_wins(self):
        service = ResumeStrategyService(AsyncSession.__new__(AsyncSession))
        settings = UserAISettings(
            resume_strategy=RESUME_STRATEGY_USE_EXISTING, save_generated_resumes=SAVE_GENERATED_SUBMITTED_ONLY
        )
        service.get_settings = _async_return(settings)
        assert await service.resolve_strategy(uuid.uuid4(), RESUME_STRATEGY_GENERATE) == RESUME_STRATEGY_GENERATE

    @pytest.mark.asyncio
    async def test_global_settings_used_when_no_override(self):
        service = ResumeStrategyService(AsyncSession.__new__(AsyncSession))
        settings = UserAISettings(
            resume_strategy=RESUME_STRATEGY_TAILOR, save_generated_resumes=SAVE_GENERATED_SUBMITTED_ONLY
        )
        service.get_settings = _async_return(settings)
        assert await service.resolve_strategy(uuid.uuid4(), None) == RESUME_STRATEGY_TAILOR


def _async_return(value):
    async def _wrapped(*args, **kwargs):
        return value

    return _wrapped


# ── Integration Tests (PostgreSQL) ──


class TestSettingsEndToEnd:
    async def test_get_or_create_defaults(self, session):
        user = await _create_user(session)
        settings = await ResumeStrategyService(session).get_settings(user.id)
        assert settings.resume_strategy == RESUME_STRATEGY_TAILOR
        assert settings.save_generated_resumes == SAVE_GENERATED_SUBMITTED_ONLY
        assert settings.user_id == user.id

    async def test_update_settings(self, session):
        user = await _create_user(session)
        service = ResumeStrategyService(session)
        updated = await service.update_settings(user.id, resume_strategy=RESUME_STRATEGY_GENERATE)
        assert updated.resume_strategy == RESUME_STRATEGY_GENERATE
        saved = await UserAISettingsRepository(session).get_by_user(user.id)
        assert saved.resume_strategy == RESUME_STRATEGY_GENERATE

    async def test_update_invalid_strategy_raises(self, session):
        user = await _create_user(session)
        with pytest.raises(ValidationError):
            await ResumeStrategyService(session).update_settings(user.id, resume_strategy="nonsense")

    async def test_settings_row_is_unique_per_user(self, session):
        user = await _create_user(session)
        service = ResumeStrategyService(session)
        first = await service.get_settings(user.id)
        second = await service.get_settings(user.id)
        assert first.id == second.id


class TestPrepareUseExisting:
    async def test_use_existing_with_explicit_resume(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        resume = await _create_master_resume(session, user.id)
        result = await ResumeStrategyService(session).prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING, resume_id=resume.id
        )
        assert result["needs_choice"] is False
        assert result["selected_resume_id"] == resume.id
        assert result["generated_resume_id"] is None
        assert result["cover_letter_id"] is not None

        app = await session.get(Application, result["application_id"])
        assert app.resume_id == resume.id
        assert app.resume_strategy == RESUME_STRATEGY_USE_EXISTING
        assert app.generated is False
        assert app.tailored is False
        assert app.status == "Ready for Review"

    async def test_use_existing_auto_selects_best(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        await _create_master_resume(session, user.id, version=1, title="Weak", text="excel word")
        good = await _create_master_resume(
            session, user.id, version=2, title="Strong",
            text="python, docker, fastapi, postgresql, sqlalchemy and kubernetes",
        )
        result = await ResumeStrategyService(session).prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING
        )
        assert result["selected_resume_id"] == good.id

    async def test_use_existing_no_resumes_raises(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        with pytest.raises(NoResumeAvailableError) as exc:
            await ResumeStrategyService(session).prepare_application(
                user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING
            )
        assert exc.value.details == {"options": ["upload", "generate"]}

    async def test_explicit_resume_from_other_user_raises(self, session, mock_ai):
        user = await _create_user(session)
        other = await _create_user(session, email="other@test.com")
        job = await _create_job(session)
        resume = await _create_master_resume(session, other.id)
        with pytest.raises(NotFoundError):
            await ResumeStrategyService(session).prepare_application(
                user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING, resume_id=resume.id
            )


class TestPrepareTailor:
    async def test_tailor_creates_generated_resume(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        master = await _create_master_resume(session, user.id, text="Senior developer python fastapi")
        result = await ResumeStrategyService(session).prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR
        )
        assert result["needs_choice"] is False
        assert result["reused_generated"] is False
        assert result["generated_resume_id"] is not None

        generated = await session.get(ResumeVersion, result["generated_resume_id"])
        assert generated.origin == "ai_tailored"
        assert generated.parent_resume_id == master.id
        assert generated.generated_for_job_id == job.id
        assert generated.resume_type == "tailored"
        assert generated.generation_metadata["mode"] == "tailor"
        assert generated.generation_metadata["job_fingerprint"] == ResumeStrategyService._job_fingerprint(job)

        app = await session.get(Application, result["application_id"])
        assert app.original_resume_id == master.id
        assert app.generated_resume_id == generated.id
        assert app.generated is True
        assert app.tailored is True
        assert app.resume_strategy == RESUME_STRATEGY_TAILOR

    async def test_tailor_no_resume_raises(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        with pytest.raises(NoResumeAvailableError) as exc:
            await ResumeStrategyService(session).prepare_application(
                user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR
            )
        assert exc.value.details == {"options": ["generate", "upload"]}

    async def test_tailor_reuses_when_inputs_unchanged(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        first = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR)
        assert first["reused_generated"] is False
        second = await service.prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR, resume_id=first["selected_resume_id"]
        )
        assert second["reused_generated"] is True
        assert second["generated_resume_id"] == first["generated_resume_id"]
        resumes = await ResumeVersionRepository(session).list_by_user_and_origins(user.id, ["ai_tailored", "ai_generated"])
        assert len(resumes) == 1

    async def test_tailor_regenerates_when_job_changes(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        other_job = await _create_job(session, title="Frontend Engineer", description="react, typescript")
        await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        first = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR)
        second = await service.prepare_application(user.id, other_job.id, strategy_override=RESUME_STRATEGY_TAILOR)
        assert second["reused_generated"] is False
        assert second["generated_resume_id"] != first["generated_resume_id"]


class TestPrepareGenerate:
    async def test_generate_from_profile(self, session, mock_ai):
        user = await _create_user(session)
        session.add(CareerProfile(user_id=user.id, headline="Python Engineer", professional_summary="Loves python."))
        await session.flush()
        job = await _create_job(session)
        result = await ResumeStrategyService(session).prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_GENERATE
        )
        assert result["needs_choice"] is False
        assert result["generated_resume_id"] is not None
        generated = await session.get(ResumeVersion, result["generated_resume_id"])
        assert generated.origin == "ai_generated"
        assert generated.generated_for_job_id == job.id
        assert generated.resume_type == "generated"

    async def test_generate_without_profile_still_works(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        result = await ResumeStrategyService(session).prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_GENERATE
        )
        assert result["generated_resume_id"] is not None

    async def test_generate_reuses_when_inputs_unchanged(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        service = ResumeStrategyService(session)
        first = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_GENERATE)
        second = await service.prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_GENERATE, resume_id=first["selected_resume_id"]
        )
        assert second["reused_generated"] is True
        assert second["generated_resume_id"] == first["generated_resume_id"]


class TestAskStrategy:
    async def test_ask_returns_needs_choice_without_application(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        await _create_master_resume(session, user.id)
        result = await ResumeStrategyService(session).prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_ASK
        )
        assert result["needs_choice"] is True
        assert result["selected_resume_id"] is not None
        assert set(result["options"]) == {
            RESUME_STRATEGY_USE_EXISTING,
            RESUME_STRATEGY_TAILOR,
            RESUME_STRATEGY_GENERATE,
        }
        from database.repositories import ApplicationRepository

        assert await ApplicationRepository(session).exists(user.id, job.id) is False

    async def test_ask_without_override_returns_needs_choice(self, session, mock_ai):
        user = await _create_user(session)
        session.add(UserAISettings(user_id=user.id, resume_strategy=RESUME_STRATEGY_ASK))
        await session.flush()
        job = await _create_job(session)
        result = await ResumeStrategyService(session).prepare_application(user.id, job.id)
        assert result["needs_choice"] is True

    async def test_ask_followed_by_explicit_strategy(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        resume = await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        asked = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_ASK)
        assert asked["needs_choice"] is True
        chosen = await service.prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING, resume_id=asked["selected_resume_id"]
        )
        assert chosen["needs_choice"] is False
        assert chosen["selected_resume_id"] == resume.id


class TestPrepareGuardrails:
    async def test_duplicate_application_raises_conflict(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        resume = await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        await service.prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING, resume_id=resume.id
        )
        with pytest.raises(ConflictError):
            await service.prepare_application(
                user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING, resume_id=resume.id
            )

    async def test_missing_job_raises_not_found(self, session, mock_ai):
        user = await _create_user(session)
        with pytest.raises(NotFoundError):
            await ResumeStrategyService(session).prepare_application(
                user.id, uuid.uuid4(), strategy_override=RESUME_STRATEGY_USE_EXISTING
            )


class TestSaveGeneratedPolicy:
    async def test_submitted_only_keeps_on_submit(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        result = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR)
        app = await session.get(Application, result["application_id"])
        await service.finalize_application(app, submitted=True)
        assert app.generated_resume_id is not None
        assert app.generated is True

    async def test_submitted_only_deletes_on_cancel(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        result = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR)
        app = await session.get(Application, result["application_id"])
        await service.finalize_application(app, submitted=False)
        assert app.generated_resume_id is None
        assert app.generated is False
        assert app.resume_id == app.original_resume_id
        assert await session.get(ResumeVersion, result["generated_resume_id"]) is None

    async def test_never_deletes_even_on_submit(self, session, mock_ai):
        user = await _create_user(session)
        session.add(
            UserAISettings(
                user_id=user.id,
                resume_strategy=RESUME_STRATEGY_TAILOR,
                save_generated_resumes=SAVE_GENERATED_NEVER,
            )
        )
        await session.flush()
        job = await _create_job(session)
        await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        result = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR)
        app = await session.get(Application, result["application_id"])
        await service.finalize_application(app, submitted=True)
        assert app.generated_resume_id is None
        assert await session.get(ResumeVersion, result["generated_resume_id"]) is None

    async def test_every_keeps_even_on_cancel(self, session, mock_ai):
        user = await _create_user(session)
        session.add(
            UserAISettings(
                user_id=user.id,
                resume_strategy=RESUME_STRATEGY_TAILOR,
                save_generated_resumes=SAVE_GENERATED_EVERY,
            )
        )
        await session.flush()
        job = await _create_job(session)
        await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        result = await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_TAILOR)
        app = await session.get(Application, result["application_id"])
        await service.finalize_application(app, submitted=False)
        assert app.generated_resume_id is not None
        assert await session.get(ResumeVersion, result["generated_resume_id"]) is not None

    async def test_finalize_noop_without_generated_resume(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        resume = await _create_master_resume(session, user.id)
        service = ResumeStrategyService(session)
        result = await service.prepare_application(
            user.id, job.id, strategy_override=RESUME_STRATEGY_USE_EXISTING, resume_id=resume.id
        )
        app = await session.get(Application, result["application_id"])
        await service.finalize_application(app, submitted=False)
        assert app.resume_id == resume.id


class TestListing:
    async def test_list_master_and_generated(self, session, mock_ai):
        user = await _create_user(session)
        job = await _create_job(session)
        await _create_master_resume(session, user.id, version=1, title="Master A")
        await _create_master_resume(session, user.id, version=2, title="Master B")
        service = ResumeStrategyService(session)
        await service.prepare_application(user.id, job.id, strategy_override=RESUME_STRATEGY_GENERATE)
        masters = await service.list_master_resumes(user.id)
        generated = await service.list_generated_resumes(user.id)
        assert len(masters) == 2
        assert all(r.origin == "master" for r in masters)
        assert len(generated) == 1
        assert generated[0].origin == "ai_generated"
        assert generated[0].generated_for_job_id == job.id
