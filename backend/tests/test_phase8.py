"""Tests for Phase 8: ATS resume optimization, keyword optimization, cover letter generation."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import get_password_hash
from app.main import app
from app.repositories.user import UserRepository
from app.schemas.cover_letter import (
    CoverLetterExportRequest,
    CoverLetterGenerateRequest,
    CoverLetterListItem,
    CoverLetterResponse,
)
from app.schemas.resume_optimizer import (
    AtsOptimizeRequest,
    AtsOptimizeResponse,
    AtsScoreResponse,
    KeywordAnalysisRequest,
    KeywordAnalysisResponse,
    KeywordMatch,
    KeywordSuggestion,
    OptimizedSection,
    OptimizeResumeRequest,
    SectionScore,
)
from app.services.ats_resume_generator import ATSResumeGenerator
from app.services.company_research import CompanyResearchService
from app.services.cover_letter_generator import CoverLetterGenerator
from app.services.resume_keyword_optimizer import ResumeKeywordOptimizer
from app.services.resume_optimizer import ResumeOptimizer


@pytest_asyncio.fixture
async def test_user(session):
    repo = UserRepository(session)
    user = await repo.create(
        email="phase8_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Phase8 Test User",
    )
    return user


@pytest_asyncio.fixture
async def auth_client(test_user, session):
    from app.api.deps import get_current_user

    async def override_get_db():
        yield session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ── Schemas ──


class TestPhase8Schemas:
    def test_optimize_resume_request(self):
        req = OptimizeResumeRequest(
            resume_version_id="00000000-0000-0000-0000-000000000001",
            job_description="Looking for a Python developer with 5 years experience",
            company_name="Acme Corp",
            job_title="Senior Python Developer",
        )
        assert str(req.resume_version_id) == "00000000-0000-0000-0000-000000000001"
        assert req.company_name == "Acme Corp"

    def test_keyword_match(self):
        km = KeywordMatch(keyword="Python", category="technical", found=True, frequency=3, importance="high")
        assert km.keyword == "Python"
        assert km.importance == "high"

    def test_section_score(self):
        ss = SectionScore(
            section="experience",
            score=75,
            matched_keywords=[KeywordMatch(keyword="Python", category="technical", found=True)],
            missing_keywords=[KeywordMatch(keyword="Kubernetes", category="technical", found=False)],
            suggestions=["Add Kubernetes experience"],
        )
        assert ss.score == 75
        assert len(ss.matched_keywords) == 1
        assert len(ss.missing_keywords) == 1

    def test_ats_score_response(self):
        resp = AtsScoreResponse(
            overall_score=85,
            recommendations=["Add more technical keywords"],
        )
        assert resp.overall_score == 85
        assert len(resp.recommendations) == 1

    def test_optimized_section(self):
        os_ = OptimizedSection(
            section="summary",
            original_text="I am a developer",
            optimized_text="I am an experienced Python developer",
            keywords_added=["Python"],
            keywords_kept=["developer"],
        )
        assert os_.keywords_added == ["Python"]

    def test_keyword_analysis_request(self):
        req = KeywordAnalysisRequest(
            resume_version_id="00000000-0000-0000-0000-000000000001",
            job_description="Need Python and Java developer",
        )
        assert "Python" in req.job_description

    def test_keyword_analysis_response(self):
        resp = KeywordAnalysisResponse(
            job_keywords=[KeywordSuggestion(keyword="Python", category="technical")],
            present_in_resume=["Python"],
            missing_from_resume=[KeywordSuggestion(keyword="Java", category="technical")],
            coverage_percentage=50.0,
            suggestions=["Add Java"],
        )
        assert resp.coverage_percentage == 50.0

    def test_ats_optimize_request(self):
        req = AtsOptimizeRequest(
            resume_version_id="00000000-0000-0000-0000-000000000001",
            job_description="Looking for a Python developer",
            company_name="Acme",
            job_title="Python Dev",
        )
        assert req.company_name == "Acme"

    def test_ats_optimize_response(self):
        resp = AtsOptimizeResponse(
            optimized_snapshot={"profile": {"full_name": "John"}},
            changes_summary="Optimized for ATS",
            keywords_injected=["Python", "Django"],
            score_improvement=20,
        )
        assert resp.score_improvement == 20

    def test_cover_letter_generate_request(self):
        req = CoverLetterGenerateRequest(
            job_title="Engineer",
            company_name="Acme",
            job_description="Looking for an engineer",
            tone="professional",
            length="medium",
        )
        assert req.job_title == "Engineer"
        assert req.tone == "professional"

    def test_cover_letter_response(self):
        from datetime import datetime, timezone
        resp = CoverLetterResponse(
            id="00000000-0000-0000-0000-000000000001",
            user_id="00000000-0000-0000-0000-000000000002",
            company_name="Acme",
            job_title="Engineer",
            content="Dear Hiring Team...",
            version=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert resp.company_name == "Acme"
        assert resp.version == 1

    def test_cover_letter_list_item(self):
        from datetime import datetime, timezone
        item = CoverLetterListItem(
            id="00000000-0000-0000-0000-000000000001",
            company_name="Acme",
            job_title="Engineer",
            version=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        assert item.company_name == "Acme"

    def test_cover_letter_export_request(self):
        req = CoverLetterExportRequest(
            cover_letter_id="00000000-0000-0000-0000-000000000001",
            format="pdf",
        )
        assert req.format == "pdf"

    def test_cover_letter_export_request_docx(self):
        req = CoverLetterExportRequest(
            cover_letter_id="00000000-0000-0000-0000-000000000001",
            format="docx",
        )
        assert req.format == "docx"

    def test_optimize_resume_request_minimal(self):
        req = OptimizeResumeRequest(
            resume_version_id="00000000-0000-0000-0000-000000000001",
            job_description="Need a developer",
        )
        assert req.target_ats_score is None

    def test_keyword_suggestion(self):
        ks = KeywordSuggestion(
            keyword="Docker",
            category="technical",
            suggested_section="experience",
            priority="high",
            reason="Required in job description",
        )
        assert ks.priority == "high"

    def test_invalid_cover_letter_tone(self):
        with pytest.raises(ValueError):
            CoverLetterGenerateRequest(
                job_title="Engineer",
                company_name="Acme",
                job_description="desc",
                tone="invalid_tone",
            )

    def test_invalid_cover_letter_length(self):
        with pytest.raises(ValueError):
            CoverLetterGenerateRequest(
                job_title="Engineer",
                company_name="Acme",
                job_description="desc",
                length="invalid",
            )


# ── CompanyResearchService ──


class TestCompanyResearchService:
    @pytest.mark.asyncio
    async def test_research_with_llm(self):
        svc = CompanyResearchService()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "company_name": "Acme", "industry": "Tech", "values": ["Innovation"],
            "products_or_services": ["Software"], "mission": "Build great software",
            "company_culture": "Fast paced", "recent_news": ["Launched new product"],
            "headquarters": "SF", "company_size": "1000", "linkedin_url": None
        })
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_response)

        with patch("app.services.company_research.get_llm_client", return_value=mock_client):
            result = await svc.research("Acme")

        assert result["company_name"] == "Acme"
        assert result["industry"] == "Tech"
        assert "Innovation" in result["values"]

    @pytest.mark.asyncio
    async def test_research_no_llm(self):
        svc = CompanyResearchService()
        with patch("app.services.company_research.get_llm_client", return_value=None):
            result = await svc.research("Unknown Corp")
        assert result["company_name"] == "Unknown Corp"
        assert result["industry"] is None

    @pytest.mark.asyncio
    async def test_research_llm_fails(self):
        svc = CompanyResearchService()
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.company_research.get_llm_client", return_value=mock_client):
            result = await svc.research("Acme")
        assert result["company_name"] == "Acme"
        assert result["industry"] is None

    @pytest.mark.asyncio
    async def test_research_bad_json(self):
        svc = CompanyResearchService()
        mock_response = MagicMock()
        mock_response.content = "not valid json"
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_response)

        with patch("app.services.company_research.get_llm_client", return_value=mock_client):
            result = await svc.research("Acme")
        assert result["company_name"] == "Acme"
        assert result["mission"] is None

    def test_fallback_info(self):
        svc = CompanyResearchService()
        fallback = svc._fallback_info("Test Corp")
        assert fallback["company_name"] == "Test Corp"
        assert fallback["values"] == []
        assert fallback["linkedin_url"] is None


# ── ResumeOptimizer ──


class TestResumeOptimizer:
    def make_snapshot(self):
        return {
            "profile": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "headline": "Senior Python Developer",
                "bio": "Experienced Python developer with 5 years in backend development.",
            },
            "experience": [
                {
                    "company": "Tech Corp",
                    "title": "Python Developer",
                    "description": "Developed APIs using Python and Django",
                    "start_date": "2020-01-01",
                    "end_date": "2023-01-01",
                }
            ],
            "education": [{"institution": "MIT", "degree": "BS", "field_of_study": "CS"}],
            "skills": [{"name": "Python", "category": "language"}, {"name": "Django", "category": "framework"}],
            "projects": [],
            "certifications": [],
            "languages": [],
            "portfolio_items": [],
        }

    def test_snapshot_to_text(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        text = optimizer._snapshot_to_text(self.make_snapshot())
        assert "Python" in text
        assert "Django" in text
        assert "MIT" in text
        assert "Tech Corp" in text

    def test_calc_keyword_score_all_match(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        matched = [KeywordMatch(keyword="Python", found=True)]
        missing = []
        assert optimizer._calc_keyword_score(matched, missing) == 100

    def test_calc_keyword_score_half_match(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        matched = [KeywordMatch(keyword="Python", found=True)]
        missing = [KeywordMatch(keyword="Java", found=False)]
        assert optimizer._calc_keyword_score(matched, missing) == 50

    def test_calc_keyword_score_none(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        assert optimizer._calc_keyword_score([], []) == 100

    def test_regex_extract_keywords(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        keywords = optimizer._regex_extract_keywords("Looking for a Python developer with Django experience")
        assert any(k.keyword == "python" for k in keywords)
        assert any(k.keyword == "django" for k in keywords)

    def test_check_format_issues_complete(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        issues = optimizer._check_format_issues(self.make_snapshot())
        assert len(issues) == 0

    def test_check_format_issues_missing_fields(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        issues = optimizer._check_format_issues({})
        assert len(issues) >= 2

    def test_generate_recommendations_with_missing(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        missing = [KeywordMatch(keyword="Kubernetes", category="technical", found=False)]
        recs = optimizer._generate_recommendations(missing, self.make_snapshot())
        assert len(recs) >= 1

    @pytest.mark.asyncio
    async def test_analyze_keywords_version_not_found(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        optimizer.resume_service.get_version = AsyncMock(return_value=None)

        result = await optimizer.analyze_keywords(
            "00000000-0000-0000-0000-000000000001",
            "Need Python developer",
        )
        assert result["coverage_percentage"] == 0.0
        assert "not found" in result["suggestions"][0]

    @pytest.mark.asyncio
    async def test_score_resume_no_llm(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        mock_version = MagicMock()
        mock_version.snapshot_data = self.make_snapshot()
        optimizer.resume_service.get_version = AsyncMock(return_value=mock_version)

        with patch.object(optimizer, "_extract_keywords_from_jd") as mock_extract:
            mock_extract.return_value = [KeywordMatch(keyword="Python", category="technical", found=True, frequency=1)]
            result = await optimizer.score_resume(
                "00000000-0000-0000-0000-000000000001",
                "Need Python developer",
            )
        assert isinstance(result, AtsScoreResponse)
        assert result.overall_score >= 0

    @pytest.mark.asyncio
    async def test_optimize_no_llm(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        mock_version = MagicMock()
        mock_version.snapshot_data = self.make_snapshot()
        optimizer.resume_service.get_version = AsyncMock(return_value=mock_version)

        with patch("app.services.resume_optimizer.get_llm_client", return_value=None):
            result = await optimizer.optimize(
                "00000000-0000-0000-0000-000000000001",
                "Need Python developer",
            )
        assert "No LLM client" in result["changes_summary"]

    @pytest.mark.asyncio
    async def test_optimize_version_not_found(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        optimizer.resume_service.get_version = AsyncMock(return_value=None)

        result = await optimizer.optimize(
            "00000000-0000-0000-0000-000000000001",
            "Need Python developer",
        )
        assert "not found" in result["changes_summary"]

    @pytest.mark.asyncio
    async def test_llm_extract_keywords_no_client(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        with patch("app.services.resume_optimizer.get_llm_client", return_value=None):
            result = await optimizer._llm_extract_keywords("Python developer needed")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_analyze_keywords_with_data(self):
        session = MagicMock()
        optimizer = ResumeOptimizer(session)
        mock_version = MagicMock()
        mock_version.snapshot_data = self.make_snapshot()
        optimizer.resume_service.get_version = AsyncMock(return_value=mock_version)

        with patch.object(optimizer, "_extract_keywords_from_jd") as mock_extract:
            mock_extract.return_value = [
                KeywordMatch(keyword="Python", category="technical", found=True, frequency=2),
                KeywordMatch(keyword="Kubernetes", category="technical", found=False, frequency=1),
            ]
            result = await optimizer.analyze_keywords(
                "00000000-0000-0000-0000-000000000001",
                "Need Python and Kubernetes developer",
            )
        assert "Python" in result["present_in_resume"]
        assert result["coverage_percentage"] == 50.0


# ── ResumeKeywordOptimizer ──


class TestResumeKeywordOptimizer:
    @pytest.mark.asyncio
    async def test_optimize_section_no_llm(self):
        optimizer = ResumeKeywordOptimizer()
        with patch("app.services.resume_keyword_optimizer.get_llm_client", return_value=None):
            result = await optimizer.optimize_section("summary", "I am a developer", ["Python"])
        assert result["optimized_text"] == "I am a developer"
        assert result["keywords_added"] == []

    @pytest.mark.asyncio
    async def test_optimize_section_with_llm(self):
        optimizer = ResumeKeywordOptimizer()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "optimized_text": "I am a Python developer with experience in Django",
            "keywords_added": ["Python", "Django"], "keywords_kept": ["developer"]
        })
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_response)

        with patch("app.services.resume_keyword_optimizer.get_llm_client", return_value=mock_client):
            result = await optimizer.optimize_section("summary", "I am a developer", ["Python", "Django"])
        assert "Python" in result["optimized_text"]
        assert "Python" in result["keywords_added"]

    @pytest.mark.asyncio
    async def test_optimize_section_llm_fails(self):
        optimizer = ResumeKeywordOptimizer()
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.resume_keyword_optimizer.get_llm_client", return_value=mock_client):
            result = await optimizer.optimize_section("summary", "I am a developer", ["Python"])
        assert result["optimized_text"] == "I am a developer"

    @pytest.mark.asyncio
    async def test_optimize_full_resume_empty(self):
        optimizer = ResumeKeywordOptimizer()
        with patch("app.services.resume_keyword_optimizer.get_llm_client", return_value=None):
            results = await optimizer.optimize_full_resume(
                {"profile": {}, "experience": [], "skills": [], "projects": []}, ["Python"]
            )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_optimize_full_resume_with_data(self):
        optimizer = ResumeKeywordOptimizer()
        snapshot = {
            "profile": {"full_name": "John", "headline": "Dev", "bio": "I am a developer"},
            "experience": [{"company": "Acme", "title": "Dev", "description": "Built stuff"}],
            "skills": [{"name": "Python"}],
            "projects": [{"name": "Project X", "description": "A cool project"}],
        }

        with patch.object(optimizer, "optimize_section") as mock_opt:
            mock_opt.return_value = {
                "section": "summary", "original_text": "text", "optimized_text": "optimized",
                "keywords_added": ["Python"], "keywords_kept": []
            }
            results = await optimizer.optimize_full_resume(snapshot, ["Python"])
        assert len(results) >= 3


# ── ATSResumeGenerator ──


class TestATSResumeGenerator:
    def make_snapshot(self):
        return {
            "profile": {
                "full_name": "John Doe", "email": "john@example.com",
                "headline": "Python Developer", "bio": "Experienced Python developer."
            },
            "experience": [
                {"company": "Tech Corp", "title": "Python Developer",
                 "description": "Built APIs with Django"}
            ],
            "education": [{"institution": "MIT", "degree": "BS", "field_of_study": "CS"}],
            "skills": [{"name": "Python"}, {"name": "Django"}],
            "projects": [],
            "certifications": [],
            "languages": [],
            "portfolio_items": [],
        }

    def test_estimate_ats_score(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        score = gen._estimate_ats_score(self.make_snapshot(), "Looking for Python Django developer")
        assert score > 0

    def test_estimate_ats_score_no_match(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        score = gen._estimate_ats_score(self.make_snapshot(), "Looking for Rust developer")
        assert score == 50  # No tech skills matched, returns default 50

    def test_snapshot_to_text(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        text = gen._snapshot_to_text(self.make_snapshot())
        assert "Python" in text
        assert "Django" in text

    @pytest.mark.asyncio
    async def test_generate_ats_optimized_no_version(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        gen.resume_service.get_version = AsyncMock(return_value=None)

        result = await gen.generate_ats_optimized(
            "00000000-0000-0000-0000-000000000001",
            "Need Python dev",
        )
        assert result.optimized_snapshot == {}
        assert "not found" in result.changes_summary

    @pytest.mark.asyncio
    async def test_generate_ats_optimized_no_llm(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        mock_version = MagicMock()
        mock_version.snapshot_data = self.make_snapshot()
        gen.resume_service.get_version = AsyncMock(return_value=mock_version)

        with patch("app.services.ats_resume_generator.get_llm_client", return_value=None):
            result = await gen.generate_ats_optimized(
                "00000000-0000-0000-0000-000000000001",
                "Need Python dev",
            )
        assert "No LLM client" in result.changes_summary
        assert result.optimized_snapshot is not None

    @pytest.mark.asyncio
    async def test_generate_ats_optimized_with_llm(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        mock_version = MagicMock()
        mock_version.snapshot_data = self.make_snapshot()
        gen.resume_service.get_version = AsyncMock(return_value=mock_version)

        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "optimized_snapshot": {
                "profile": {
                    "full_name": "John Doe", "email": "john@example.com",
                    "headline": "Senior Python Developer",
                    "bio": "Experienced Python developer with expertise in Django."
                },
                "experience": [
                    {"company": "Tech Corp", "title": "Python Developer",
                     "description": "Developed scalable APIs using Python and Django"}
                ],
                "skills": [{"name": "Python"}, {"name": "Django"}, {"name": "REST APIs"}]
            },
            "changes_summary": "Enhanced summary to highlight Python expertise, "
                               "rewrote experience to emphasize API development",
            "keywords_injected": ["REST APIs", "scalable"]
        })
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_response)

        with patch("app.services.ats_resume_generator.get_llm_client", return_value=mock_client):
            result = await gen.generate_ats_optimized(
                "00000000-0000-0000-0000-000000000001",
                "Need Python Django developer with REST API experience",
                company_name="Acme",
                job_title="Senior Python Dev",
            )
        assert isinstance(result, AtsOptimizeResponse)
        assert "REST APIs" in result.keywords_injected
        assert result.score_improvement >= 0

    @pytest.mark.asyncio
    async def test_rewrite_for_ats_fails(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(side_effect=Exception("API failed"))

        result = await gen._rewrite_for_ats(self.make_snapshot(), "Need Python dev", None, None, mock_client)
        assert "failed" in result["changes_summary"]

    @pytest.mark.asyncio
    async def test_rewrite_for_ats_bad_json(self):
        session = MagicMock()
        gen = ATSResumeGenerator(session)
        mock_response = MagicMock()
        mock_response.content = "not valid json"
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_response)

        result = await gen._rewrite_for_ats(self.make_snapshot(), "Need Python dev", None, None, mock_client)
        assert "failed" in result["changes_summary"]


# ── CoverLetterGenerator ──


class TestCoverLetterGenerator:
    @pytest.mark.asyncio
    async def test_generate_with_llm(self):
        session = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        gen = CoverLetterGenerator(session)
        gen.repo.create = AsyncMock(
            return_value=MagicMock(
                id="00000000-0000-0000-0000-000000000001",
                user_id="00000000-0000-0000-0000-000000000002",
                job_posting_id=None,
                company_name="Acme Corp",
                job_title="Software Engineer",
                hiring_manager_name=None,
                content="Dear Hiring Team, I am excited...",
                version=1,
                file_path=None,
                file_format=None,
                is_active=True,
            )
        )
        gen._get_max_version = AsyncMock(return_value=0)

        mock_response = MagicMock()
        mock_response.content = (
            "Dear Hiring Team,\n\nI am excited to apply for the Software Engineer role "
            "at Acme Corp..."
        )
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_response)

        with (
            patch("app.services.cover_letter_generator.get_llm_client", return_value=mock_client),
            patch.object(gen.company_research, "research", AsyncMock(return_value={
                "company_name": "Acme Corp", "mission": "Build great software",
                "values": ["Innovation"]
            }))
        ):
            cl = await gen.generate(
                user_id="00000000-0000-0000-0000-000000000002",
                    job_title="Software Engineer",
                    company_name="Acme Corp",
                    job_description="Looking for a software engineer with Python skills",
                    user_full_name="John Doe",
                    current_role="Senior Developer",
                    years_experience=5,
                    field="Software Engineering",
                    key_skills="Python, Django",
                    relevant_experience="Built scalable APIs",
                    reason_for_interest="Love your mission",
                )
        assert cl.company_name == "Acme Corp"
        assert cl.job_title == "Software Engineer"
        assert cl.version == 1

    @pytest.mark.asyncio
    async def test_generate_no_llm_fallback(self):
        session = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        gen = CoverLetterGenerator(session)
        gen.repo.create = AsyncMock(
            return_value=MagicMock(
                id="00000000-0000-0000-0000-000000000001",
                user_id="00000000-0000-0000-0000-000000000002",
                company_name="Acme Corp",
                job_title="Engineer",
                content="Fallback letter",
                version=1,
                is_active=True,
            )
        )
        gen._get_max_version = AsyncMock(return_value=0)

        with patch("app.services.cover_letter_generator.get_llm_client", return_value=None):
            cl = await gen.generate(
                user_id="00000000-0000-0000-0000-000000000002",
                job_title="Engineer",
                company_name="Acme Corp",
                job_description="desc",
            )
        assert "Dear" in cl.content or cl.content == "Fallback letter"

    @pytest.mark.asyncio
    async def test_generate_llm_fails(self):
        session = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        gen = CoverLetterGenerator(session)
        gen._get_max_version = AsyncMock(return_value=0)

        actual_create_args = {}

        async def fake_create(**kwargs):
            actual_create_args.update(kwargs)
            mock = MagicMock(
                id="00000000-0000-0000-0000-000000000001",
                user_id=kwargs.get("user_id"),
                company_name=kwargs.get("company_name"),
                job_title=kwargs.get("job_title"),
                content=kwargs.get("content", ""),
                version=kwargs.get("version", 1),
                is_active=True,
            )
            return mock

        gen.repo.create = AsyncMock(side_effect=fake_create)
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(side_effect=Exception("API error"))

        with patch("app.services.cover_letter_generator.get_llm_client", return_value=mock_client):
            cl = await gen.generate(
                user_id="00000000-0000-0000-0000-000000000002",
                job_title="Engineer",
                company_name="Acme",
                job_description="desc",
                user_full_name="John",
                current_role="Dev",
            )
        assert "Dear" in cl.content

    def test_fallback_template(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        result = gen._fallback_template("Engineer", "Acme", "Jane Doe", "John", "Developer")
        assert "Jane Doe" in result
        assert "Engineer" in result
        assert "Acme" in result
        assert "John" in result

    @pytest.mark.asyncio
    async def test_list_cover_letters(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        result = await gen.list_cover_letters("00000000-0000-0000-0000-000000000001")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_cover_letter_found(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        mock_cl = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_cl
        session.execute = AsyncMock(return_value=mock_result)

        cl = await gen.get_cover_letter("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002")
        assert cl is not None

    @pytest.mark.asyncio
    async def test_get_cover_letter_not_found(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        cl = await gen.get_cover_letter("00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002")
        assert cl is None

    @pytest.mark.asyncio
    async def test_delete_cover_letter_found(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        mock_cl = MagicMock()
        gen.get_cover_letter = AsyncMock(return_value=mock_cl)
        session.delete = AsyncMock()
        session.flush = AsyncMock()

        uid1 = "00000000-0000-0000-0000-000000000001"
        uid2 = "00000000-0000-0000-0000-000000000002"
        result = await gen.delete_cover_letter(uid1, uid2)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_cover_letter_not_found(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        gen.get_cover_letter = AsyncMock(return_value=None)

        uid1 = "00000000-0000-0000-0000-000000000001"
        uid2 = "00000000-0000-0000-0000-000000000002"
        result = await gen.delete_cover_letter(uid1, uid2)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_max_version_empty(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        result = await gen._get_max_version("00000000-0000-0000-0000-000000000001")
        assert result == 0

    @pytest.mark.asyncio
    async def test_export_cover_letter_not_found(self):
        session = MagicMock()
        gen = CoverLetterGenerator(session)
        gen.get_cover_letter = AsyncMock(return_value=None)

        uid1 = "00000000-0000-0000-0000-000000000001"
        uid2 = "00000000-0000-0000-0000-000000000002"
        result = await gen.export_cover_letter(uid1, uid2)
        assert result is None

    @pytest.mark.asyncio
    async def test_export_cover_letter_pdf(self):
        session = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        gen = CoverLetterGenerator(session)
        mock_cl = MagicMock()
        mock_cl.id = "00000000-0000-0000-0000-000000000001"
        mock_cl.content = "Dear Team,"
        mock_cl.job_title = "Engineer"
        mock_cl.company_name = "Acme"
        mock_cl.version = 1
        mock_cl.file_path = None
        mock_cl.file_format = None
        gen.get_cover_letter = AsyncMock(return_value=mock_cl)

        with patch("app.services.resume_generator.ResumeGeneratorService") as MockGenSvc:  # noqa: N806
            mock_gen = MagicMock()
            mock_gen.generate_pdf.return_value = b"fake pdf content"
            MockGenSvc.return_value = mock_gen

            result = await gen.export_cover_letter(
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002",
                "pdf",
            )
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_with_resume_snapshot(self):
        session = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        gen = CoverLetterGenerator(session)
        gen.repo.create = AsyncMock(
            return_value=MagicMock(
                id="00000000-0000-0000-0000-000000000001",
                user_id="00000000-0000-0000-0000-000000000002",
                company_name="Acme",
                job_title="Engineer",
                content="Custom letter",
                version=1,
                is_active=True,
            )
        )
        gen._get_max_version = AsyncMock(return_value=0)

        with patch("app.services.cover_letter_generator.get_llm_client", return_value=None):
            cl = await gen.generate(
                user_id="00000000-0000-0000-0000-000000000002",
                job_title="Engineer",
                company_name="Acme",
                job_description="desc",
                resume_snapshot={
                    "profile": {"full_name": "John Doe", "headline": "Senior Dev"},
                    "skills": [{"name": "Python"}, {"name": "Django"}],
                    "experience": [{"company": "Tech Corp", "title": "Dev", "description": "Built stuff"}],
                },
            )
        assert cl is not None


# ── API Routes ──


class TestPhase8APIIntegration:
    @pytest.mark.asyncio
    async def test_score_resume_ats_endpoint(self, auth_client):
        master_resp = await auth_client.post(
            "/api/v1/resumes/masters",
            json={"name": "ATS Test Resume", "title": "Python Developer"},
        )
        master_id = master_resp.json()["id"]
        version_resp = await auth_client.post(
            f"/api/v1/resumes/masters/{master_id}/versions",
            json={
                "name": "v1",
                "snapshot_data": {
                    "profile": {
                        "full_name": "John Doe", "email": "john@example.com",
                        "headline": "Python Developer", "bio": "Experienced Python developer."
                    },
                    "experience": [
                        {"company": "Tech Corp", "title": "Python Developer",
                         "description": "Built APIs with Django"}
                    ],
                    "skills": [{"name": "Python"}, {"name": "Django"}],
                    "education": [],
                    "projects": [],
                    "certifications": [],
                    "languages": [],
                    "portfolio_items": [],
                },
            },
        )
        version_id = version_resp.json()["id"]

        response = await auth_client.post(
            "/api/v1/resumes/optimize/score",
            json={
                "resume_version_id": str(version_id),
                "job_description": "Looking for a Python Django developer with API experience",
                "company_name": "Acme Corp",
                "job_title": "Senior Python Developer",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert isinstance(data["overall_score"], int)
        assert 0 <= data["overall_score"] <= 100

    @pytest.mark.asyncio
    async def test_analyze_keywords_endpoint(self, auth_client):
        master_resp = await auth_client.post(
            "/api/v1/resumes/masters",
            json={"name": "Keyword Test Resume"},
        )
        master_id = master_resp.json()["id"]
        version_resp = await auth_client.post(
            f"/api/v1/resumes/masters/{master_id}/versions",
            json={
                "name": "v1",
                "snapshot_data": {
                    "profile": {"full_name": "John Doe"},
                    "experience": [],
                    "skills": [{"name": "Python"}],
                    "education": [],
                    "projects": [],
                    "certifications": [],
                    "languages": [],
                    "portfolio_items": [],
                },
            },
        )
        version_id = version_resp.json()["id"]

        response = await auth_client.post(
            "/api/v1/resumes/optimize/keywords",
            json={
                "resume_version_id": str(version_id),
                "job_description": "Looking for Python and JavaScript developer",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "coverage_percentage" in data

    @pytest.mark.asyncio
    async def test_ats_generate_endpoint(self, auth_client):
        master_resp = await auth_client.post(
            "/api/v1/resumes/masters",
            json={"name": "ATS Generate Test Resume"},
        )
        master_id = master_resp.json()["id"]
        version_resp = await auth_client.post(
            f"/api/v1/resumes/masters/{master_id}/versions",
            json={
                "name": "v1",
                "snapshot_data": {
                    "profile": {"full_name": "John Doe", "headline": "Developer"},
                    "experience": [{"company": "Acme", "title": "Dev", "description": "Built things"}],
                    "skills": [{"name": "Python"}],
                    "education": [],
                    "projects": [],
                    "certifications": [],
                    "languages": [],
                    "portfolio_items": [],
                },
            },
        )
        version_id = version_resp.json()["id"]

        response = await auth_client.post(
            "/api/v1/resumes/optimize/ats-generate",
            json={
                "resume_version_id": str(version_id),
                "job_description": "Looking for Python developer with Django experience",
                "company_name": "Acme Corp",
                "job_title": "Python Developer",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "optimized_snapshot" in data

    @pytest.mark.asyncio
    async def test_generate_cover_letter_endpoint(self, auth_client):
        response = await auth_client.post(
            "/api/v1/resumes/cover-letters/generate",
            json={
                "job_title": "Software Engineer",
                "company_name": "Acme Corp",
                "job_description": "Looking for a software engineer with Python skills",
                "user_full_name": "John Doe",
                "current_role": "Senior Developer",
                "years_experience": 5,
                "key_skills": "Python, Django",
                "relevant_experience": "Built scalable microservices",
                "tone": "professional",
                "length": "medium",
                "include_company_research": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "Acme Corp"
        assert data["job_title"] == "Software Engineer"
        assert "content" in data

    @pytest.mark.asyncio
    async def test_list_cover_letters_endpoint(self, auth_client):
        r1 = await auth_client.post(
            "/api/v1/resumes/cover-letters/generate",
            json={
                "job_title": "Engineer",
                "company_name": "Acme",
                "job_description": "Software engineer position",
                "include_company_research": False,
            },
        )
        assert r1.status_code == 201, f"Create 1 failed: {r1.text}"
        r2 = await auth_client.post(
            "/api/v1/resumes/cover-letters/generate",
            json={
                "job_title": "Manager",
                "company_name": "Corp",
                "job_description": "Engineering manager role",
                "include_company_research": False,
            },
        )
        assert r2.status_code == 201, f"Create 2 failed: {r2.text}"
        response = await auth_client.get("/api/v1/resumes/cover-letters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_cover_letter_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/resumes/cover-letters/generate",
            json={
                "job_title": "Engineer",
                "company_name": "Acme",
                "job_description": "Software engineer position",
                "include_company_research": False,
            },
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        cl_id = create_resp.json()["id"]

        response = await auth_client.get(f"/api/v1/resumes/cover-letters/{cl_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cl_id

    @pytest.mark.asyncio
    async def test_get_cover_letter_not_found(self, auth_client):
        response = await auth_client.get(f"/api/v1/resumes/cover-letters/{uuid.uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_cover_letter_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/resumes/cover-letters/generate",
            json={
                "job_title": "To Delete",
                "company_name": "Acme",
                "job_description": "Position to delete test",
                "include_company_research": False,
            },
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        cl_id = create_resp.json()["id"]

        response = await auth_client.delete(f"/api/v1/resumes/cover-letters/{cl_id}")
        assert response.status_code == 204

        response = await auth_client.get(f"/api/v1/resumes/cover-letters/{cl_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_cover_letter_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/resumes/cover-letters/generate",
            json={
                "job_title": "Export Test",
                "company_name": "Acme",
                "job_description": "Export cover letter test",
                "include_company_research": False,
            },
        )
        assert create_resp.status_code == 201, f"Create failed: {create_resp.text}"
        cl_id = create_resp.json()["id"]

        response = await auth_client.post(
            f"/api/v1/resumes/cover-letters/{cl_id}/export",
            json={"format": "pdf"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["file_format"] == "pdf"

    @pytest.mark.asyncio
    async def test_cover_letter_export_not_found(self, auth_client):
        response = await auth_client.post(
            f"/api/v1/resumes/cover-letters/{uuid.uuid4()}/export",
            json={"format": "pdf"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_optimize_score_invalid_version(self, auth_client):
        response = await auth_client.post(
            "/api/v1/resumes/optimize/score",
            json={
                "resume_version_id": str(uuid.uuid4()),
                "job_description": "Looking for a developer",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 0

    @pytest.mark.asyncio
    async def test_ats_generate_invalid_version(self, auth_client):
        response = await auth_client.post(
            "/api/v1/resumes/optimize/ats-generate",
            json={
                "resume_version_id": str(uuid.uuid4()),
                "job_description": "Looking for a developer",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["optimized_snapshot"] == {}
