"""Tests for Phase 10: Interview Preparation Engine."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_password_hash
from app.main import app
from app.repositories.user import UserRepository
from app.schemas.interview_prep import (
    BehavioralQuestion,
    CareerGoal,
    CompanySpecificAnswer,
    InterviewPrepGenerateRequest,
    InterviewPrepListItem,
    InterviewPrepResponse,
    NoticePeriodInfo,
    SalaryExpectation,
    StrengthItem,
    TechnicalQuestion,
    TruthValidateRequest,
    TruthValidateResponse,
    TruthValidationResult,
    WeaknessItem,
)
from app.services.interview_prep import InterviewPrepService
from app.services.truth_validator import TruthValidator

# ── Fixtures ──


@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(
        email="phase10_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Phase10 Test User",
    )
    return user


@pytest_asyncio.fixture
async def auth_client(test_user, session: AsyncSession):
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


def make_mock_llm_client(json_response: str | dict | list):
    if isinstance(json_response, dict | list):
        json_response = json.dumps(json_response)
    mock_resp = MagicMock()
    mock_resp.content = json_response
    mock_client = MagicMock()
    mock_client.complete = AsyncMock(return_value=mock_resp)
    return mock_client


# ── Schema Tests ──


class TestInterviewPrepSchemas:
    def test_behavioral_question(self):
        bq = BehavioralQuestion(
            question="Tell me about a conflict",
            situation="Team disagreement",
            task="Resolve issue",
            action="Mediated discussion",
            result="Team agreed",
            category="conflict",
        )
        assert bq.question == "Tell me about a conflict"

    def test_technical_question(self):
        tq = TechnicalQuestion(
            question="What is REST?",
            topic="API",
            difficulty="easy",
            answer="Representational State Transfer",
            key_concepts=["HTTP", "Stateless"],
        )
        assert tq.difficulty == "easy"

    def test_salary_expectation(self):
        se = SalaryExpectation(
            market_range_min=80000,
            market_range_max=120000,
            recommended=100000,
            factors=["Experience", "Location"],
            negotiation_tips=["Know your worth"],
        )
        assert se.recommended == 100000

    def test_notice_period(self):
        np = NoticePeriodInfo(
            current_period_weeks=4,
            negotiable=True,
            negotiation_tips=["Offer to train replacement"],
            standard_in_industry="2-4 weeks",
        )
        assert np.current_period_weeks == 4

    def test_strength_item(self):
        si = StrengthItem(
            strength="Python",
            evidence="5 years building APIs",
            relevance_to_role="Core requirement",
            category="technical",
        )
        assert si.strength == "Python"

    def test_weakness_item(self):
        wi = WeaknessItem(
            weakness="Public speaking",
            improvement_plan="Taking courses",
            positive_framing="Actively improving",
            category="skill",
        )
        assert wi.weakness == "Public speaking"

    def test_career_goal(self):
        cg = CareerGoal(
            short_term="Learn cloud",
            long_term="Become architect",
            alignment_with_company="Uses AWS",
            timeline_years=5,
        )
        assert cg.timeline_years == 5

    def test_company_specific_answer(self):
        csa = CompanySpecificAnswer(
            question="Why this company?",
            context="Mission-driven",
            suggested_answer="I admire your mission",
            research_source="Company website",
        )
        assert csa.suggested_answer == "I admire your mission"

    def test_truth_validation_result(self):
        tvr = TruthValidationResult(
            statement="I know Python",
            is_consistent=True,
            confidence=0.9,
            inconsistencies=[],
            suggestions=["Be specific"],
        )
        assert tvr.is_consistent is True

    def test_generate_request_defaults(self):
        req = InterviewPrepGenerateRequest(
            job_title="Engineer",
            company_name="Acme",
            job_description="Build software",
        )
        assert req.include_behavioral is True
        assert req.include_technical is True

    def test_response_from_attrs(self):
        uid = uuid.uuid4()
        data = {
            "id": uid,
            "user_id": uuid.uuid4(),
            "job_title": "Engineer",
            "company_name": "Acme",
            "behavioral_questions": [],
            "technical_questions": [],
            "strengths": [],
            "weaknesses": [],
            "company_specific_answers": [],
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        resp = InterviewPrepResponse(**data)
        assert resp.job_title == "Engineer"

    def test_list_item(self):
        uid = uuid.uuid4()
        li = InterviewPrepListItem(
            id=uid,
            job_title="Engineer",
            company_name="Acme",
            created_at="2024-01-01T00:00:00+00:00",
        )
        assert li.company_name == "Acme"

    def test_truth_validate_request(self):
        tvr = TruthValidateRequest(statements=["I know Python", "I built a app"])
        assert len(tvr.statements) == 2

    def test_truth_validate_response(self):
        tvr = TruthValidateResponse(
            results=[
                TruthValidationResult(
                    statement="I know Python",
                    is_consistent=True,
                    confidence=0.9,
                )
            ]
        )
        assert tvr.results[0].is_consistent is True


# ── InterviewPrepService Tests ──


class TestInterviewPrepService:
    @pytest.mark.asyncio
    async def test_generate_full(self):
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        session.execute = AsyncMock()

        svc = InterviewPrepService(session)

        behavioral_resp = [
            {"question": "Tell me about a challenge", "situation": "Hard project",
             "task": "Deliver on time", "action": "Organized team", "result": "Shipped",
             "category": "problem-solving"}
        ]
        technical_resp = [
            {"question": "What is an API?", "topic": "Web", "difficulty": "easy",
             "answer": "Application Programming Interface", "key_concepts": ["REST"]}
        ]
        salary_resp = {"market_range_min": 80000, "market_range_max": 120000,
                       "recommended": 100000, "currency": "USD", "factors": ["Exp"],
                       "negotiation_tips": ["Negotiate"]}
        notice_resp = {"current_period_weeks": 4, "negotiable": True,
                       "negotiation_tips": ["Train replacement"],
                       "standard_in_industry": "2-4 weeks"}
        sw_resp = {
            "strengths": [{"strength": "Python", "evidence": "5 years",
                           "relevance_to_role": "Core", "category": "technical"}],
            "weaknesses": [{"weakness": "Public speaking", "improvement_plan": "Courses",
                            "positive_framing": "Improving", "category": "skill"}],
        }
        career_resp = {"short_term": "Learn cloud", "long_term": "Architect",
                       "alignment_with_company": "Uses AWS", "timeline_years": 5}
        company_resp = [
            {"question": "Why us?", "context": "Mission", "suggested_answer": "Aligns",
             "research_source": "Website"}
        ]

        mock_client = MagicMock()
        mock_client.complete = AsyncMock()
        results = iter([
            behavioral_resp, technical_resp, salary_resp, notice_resp,
            sw_resp, career_resp, company_resp,
        ])

        async def side_effect(*args, **kwargs):
            mock = MagicMock()
            mock.content = json.dumps(next(results))
            return mock

        mock_client.complete = AsyncMock(side_effect=side_effect)

        with patch(
            "app.services.interview_prep.get_llm_client",
            return_value=mock_client,
        ):
            prep = await svc.generate(
                user_id=uuid.uuid4(),
                job_title="Engineer",
                company_name="Acme Corp",
                job_description="Build software with Python",
                resume_snapshot={"profile": {"headline": "Python Dev", "bio": "Experienced"},
                                 "skills": [{"name": "Python"}],
                                 "experience": [{"title": "Dev", "company": "Tech"}]},
                company_research={"industry": "Tech", "mission": "Build great software",
                                  "values": ["Innovation"], "company_culture": "Fast",
                                  "hiring_trends": ["Growing"], "technology_stack": ["Python"]},
            )

        assert prep.job_title == "Engineer"
        assert prep.company_name == "Acme Corp"
        assert len(prep.behavioral_questions) == 1
        assert len(prep.technical_questions) == 1
        assert prep.salary_expectation is not None
        assert prep.notice_period is not None
        assert len(prep.strengths) == 1
        assert len(prep.weaknesses) == 1
        assert prep.career_goals is not None
        assert len(prep.company_specific_answers) == 1

    @pytest.mark.asyncio
    async def test_generate_no_llm(self):
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()

        svc = InterviewPrepService(session)

        with patch(
            "app.services.interview_prep.get_llm_client",
            return_value=None,
        ):
            prep = await svc.generate(
                user_id=uuid.uuid4(),
                job_title="Engineer",
                company_name="Acme Corp",
                job_description="Build software",
            )

        assert prep.job_title == "Engineer"
        assert prep.company_name == "Acme Corp"
        assert prep.behavioral_questions == []
        assert prep.technical_questions == []

    @pytest.mark.asyncio
    async def test_generate_partial_flags(self):
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()

        svc = InterviewPrepService(session)

        mock_resp = MagicMock()
        mock_resp.content = json.dumps({"short_term": "Learn", "long_term": "Grow",
                                         "alignment_with_company": "Fit",
                                         "timeline_years": 3})
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_resp)

        with patch(
            "app.services.interview_prep.get_llm_client",
            return_value=mock_client,
        ):
            prep = await svc.generate(
                user_id=uuid.uuid4(),
                job_title="Engineer",
                company_name="Acme Corp",
                job_description="Build software",
                include_behavioral=False,
                include_technical=False,
                include_salary=False,
                include_notice_period=False,
                include_strengths_weaknesses=False,
                include_career_goals=True,
                include_company_specific=False,
            )

        assert prep.job_title == "Engineer"
        assert prep.behavioral_questions == []
        assert prep.technical_questions == []
        assert prep.career_goals is not None
        assert prep.salary_expectation is None

    @pytest.mark.asyncio
    async def test_build_resume_context(self):
        snapshot = {
            "profile": {"headline": "Senior Dev", "bio": "10 years exp"},
            "skills": [{"name": "Python"}, {"name": "Django"}],
            "experience": [
                {"title": "Senior", "company": "Acme"},
                {"title": "Junior", "company": "Startup"},
            ],
        }
        ctx = InterviewPrepService._build_resume_context(snapshot)
        assert "Senior Dev" in ctx
        assert "Python" in ctx
        assert "Senior at Acme" in ctx

    def test_build_resume_context_empty(self):
        ctx = InterviewPrepService._build_resume_context(None)
        assert ctx == "No resume data available."

    def test_build_company_context(self):
        research = {
            "industry": "Tech",
            "mission": "Innovate",
            "values": ["Speed"],
            "company_culture": "Fast",
            "hiring_trends": ["Growing"],
            "technology_stack": ["Python"],
        }
        ctx = InterviewPrepService._build_company_context(research)
        assert "Tech" in ctx
        assert "Innovate" in ctx

    def test_build_company_context_empty(self):
        ctx = InterviewPrepService._build_company_context(None)
        assert ctx == "No company research data available."

    @pytest.mark.asyncio
    async def test_get_found(self):
        mock_prep = MagicMock()
        mock_prep.id = uuid.uuid4()
        mock_prep.user_id = uuid.uuid4()
        mock_prep.job_title = "Engineer"

        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_prep)
        session.execute = AsyncMock(return_value=mock_result)

        svc = InterviewPrepService(session)
        prep = await svc.get(mock_prep.id, mock_prep.user_id)
        assert prep is not None
        assert prep.job_title == "Engineer"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=mock_result)

        svc = InterviewPrepService(session)
        prep = await svc.get(uuid.uuid4(), uuid.uuid4())
        assert prep is None

    @pytest.mark.asyncio
    async def test_list_by_user(self):
        mock_prep = MagicMock()
        mock_prep.job_title = "Engineer"

        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock())
        mock_result.scalars.return_value.all = MagicMock(return_value=[mock_prep])
        session.execute = AsyncMock(return_value=mock_result)

        svc = InterviewPrepService(session)
        preps = await svc.list_by_user(uuid.uuid4())
        assert len(preps) == 1

    @pytest.mark.asyncio
    async def test_delete_found(self):
        mock_prep = MagicMock()

        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_prep)
        session.execute = AsyncMock(return_value=mock_result)
        session.delete = AsyncMock()
        session.flush = AsyncMock()

        svc = InterviewPrepService(session)
        result = await svc.delete(uuid.uuid4(), uuid.uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=mock_result)

        svc = InterviewPrepService(session)
        result = await svc.delete(uuid.uuid4(), uuid.uuid4())
        assert result is False


# ── TruthValidator Tests ──


class TestTruthValidator:
    @pytest.mark.asyncio
    async def test_validate_with_llm(self):
        validator = TruthValidator()
        mock_resp = MagicMock()
        mock_resp.content = json.dumps([
            {"statement": "I know Python", "is_consistent": True,
             "confidence": 0.95, "inconsistencies": [], "suggestions": []},
            {"statement": "I built a rocket", "is_consistent": False,
             "confidence": 0.3, "inconsistencies": ["No experience"],
             "suggestions": ["Be honest"]},
        ])
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(return_value=mock_resp)

        with patch(
            "app.services.truth_validator.get_llm_client",
            return_value=mock_client,
        ):
            results = await validator.validate(
                ["I know Python", "I built a rocket"],
                "Context: software engineer interview",
            )

        assert len(results) == 2
        assert results[0]["is_consistent"] is True
        assert results[1]["is_consistent"] is False

    @pytest.mark.asyncio
    async def test_validate_no_llm(self):
        validator = TruthValidator()
        with patch(
            "app.services.truth_validator.get_llm_client",
            return_value=None,
        ):
            results = await validator.validate(["I know Python"], None)

        assert len(results) == 1
        assert results[0]["is_consistent"] is True
        assert results[0]["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_validate_empty(self):
        validator = TruthValidator()
        results = await validator.validate([], None)
        assert results == []

    @pytest.mark.asyncio
    async def test_validate_llm_fails(self):
        validator = TruthValidator()
        mock_client = MagicMock()
        mock_client.complete = AsyncMock(
            side_effect=Exception("LLM error")
        )
        with patch(
            "app.services.truth_validator.get_llm_client",
            return_value=mock_client,
        ):
            results = await validator.validate(["Statement"], None)

        assert len(results) == 1
        assert results[0]["is_consistent"] is True

    @pytest.mark.asyncio
    async def test_fallback_results(self):
        results = TruthValidator._fallback_results(["Stmt1", "Stmt2"])
        assert len(results) == 2
        for r in results:
            assert r["is_consistent"] is True
            assert r["confidence"] == 0.0


# ── API Integration Tests ──


class TestPhase10APIIntegration:
    @pytest.mark.asyncio
    async def test_generate_endpoint(self, auth_client):
        resp_data = {"short_term": "Learn", "long_term": "Lead",
                     "alignment_with_company": "Fit", "timeline_years": 5}
        mock_client = make_mock_llm_client(resp_data)

        with patch(
            "app.services.interview_prep.get_llm_client",
            return_value=mock_client,
        ):
            resp = await auth_client.post(
                "/api/v1/company/interview-prep/generate",
                json={
                    "job_title": "Software Engineer",
                    "company_name": "Acme Corp",
                    "job_description": "Looking for a Python developer",
                    "include_behavioral": False,
                    "include_technical": False,
                    "include_salary": False,
                    "include_notice_period": False,
                    "include_strengths_weaknesses": False,
                    "include_career_goals": True,
                    "include_company_specific": False,
                },
            )

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["job_title"] == "Software Engineer"
        assert data["company_name"] == "Acme Corp"

    @pytest.mark.asyncio
    async def test_list_endpoint(self, auth_client):
        mock_client = make_mock_llm_client(
            {"short_term": "X", "long_term": "Y",
             "alignment_with_company": "Z", "timeline_years": 3}
        )
        with patch(
            "app.services.interview_prep.get_llm_client",
            return_value=mock_client,
        ):
            await auth_client.post(
                "/api/v1/company/interview-prep/generate",
                json={
                    "job_title": "Engineer",
                    "company_name": "Acme",
                    "job_description": "Role description",
                    "include_behavioral": False,
                    "include_technical": False,
                    "include_salary": False,
                    "include_notice_period": False,
                    "include_strengths_weaknesses": False,
                    "include_career_goals": True,
                    "include_company_specific": False,
                },
            )

        resp = await auth_client.get("/api/v1/company/interview-prep")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_by_id_endpoint(self, auth_client):
        mock_client = make_mock_llm_client(
            {"short_term": "X", "long_term": "Y",
             "alignment_with_company": "Z", "timeline_years": 3}
        )
        with patch(
            "app.services.interview_prep.get_llm_client",
            return_value=mock_client,
        ):
            create = await auth_client.post(
                "/api/v1/company/interview-prep/generate",
                json={
                    "job_title": "Engineer",
                    "company_name": "Acme",
                    "job_description": "Role description",
                    "include_behavioral": False,
                    "include_technical": False,
                    "include_salary": False,
                    "include_notice_period": False,
                    "include_strengths_weaknesses": False,
                    "include_career_goals": True,
                    "include_company_specific": False,
                },
            )

        prep_id = create.json()["id"]
        resp = await auth_client.get(f"/api/v1/company/interview-prep/{prep_id}")
        assert resp.status_code == 200, resp.text
        assert resp.json()["job_title"] == "Engineer"

    @pytest.mark.asyncio
    async def test_get_not_found(self, auth_client):
        resp = await auth_client.get(
            f"/api/v1/company/interview-prep/{uuid.uuid4()}"
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_endpoint(self, auth_client):
        mock_client = make_mock_llm_client(
            {"short_term": "X", "long_term": "Y",
             "alignment_with_company": "Z", "timeline_years": 3}
        )
        with patch(
            "app.services.interview_prep.get_llm_client",
            return_value=mock_client,
        ):
            create = await auth_client.post(
                "/api/v1/company/interview-prep/generate",
                json={
                    "job_title": "Engineer",
                    "company_name": "Acme",
                    "job_description": "Role description",
                    "include_behavioral": False,
                    "include_technical": False,
                    "include_salary": False,
                    "include_notice_period": False,
                    "include_strengths_weaknesses": False,
                    "include_career_goals": True,
                    "include_company_specific": False,
                },
            )

        prep_id = create.json()["id"]
        resp = await auth_client.delete(
            f"/api/v1/company/interview-prep/{prep_id}"
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_truth_validate_endpoint(self, auth_client):
        mock_client = make_mock_llm_client([
            {"statement": "I know Python", "is_consistent": True,
             "confidence": 0.95, "inconsistencies": [], "suggestions": []},
        ])
        with patch(
            "app.services.truth_validator.get_llm_client",
            return_value=mock_client,
        ):
            resp = await auth_client.post(
                "/api/v1/company/interview-prep/validate-truth",
                json={
                    "statements": ["I know Python"],
                    "context": "Interview context",
                },
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["is_consistent"] is True

    @pytest.mark.asyncio
    async def test_generate_without_auth_returns_401(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/company/interview-prep/generate",
                json={
                    "job_title": "Engineer",
                    "company_name": "Acme",
                    "job_description": "Role",
                },
            )
        assert resp.status_code == 401
