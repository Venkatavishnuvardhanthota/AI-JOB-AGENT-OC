"""Tests for AI-powered feature services — Sprint 3.1 expanded coverage."""

from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.ai.features.resume import (
    ai_enhance_experience,
    ai_enhance_profile,
    ai_enhance_profile_delegated,
    ai_enhance_project,
    ai_generate_resume,
    ai_improve_resume_section,
    ai_optimize_ats,
    ai_recommend_skills,
)
from app.ai.features.cover_letter import (
    ai_assist_cover_letter,
    ai_generate_cover_letter,
)
from app.ai.features.interview import (
    ai_answer_application_questions,
    ai_generate_interview_questions,
)
from app.ai.features.company_research import (
    ai_company_research,
    ai_job_summary,
)
from app.ai.features.email import ai_generate_email
from app.ai.features.matching import ai_enhance_matching
from app.ai.features.schemas import (
    ATSOptimizeRequest,
    ApplicationQuestionsRequest,
    CompanyResearchRequest,
    CoverLetterAssistRequest,
    CoverLetterGenerateRequest,
    EmailGenerateRequest,
    ExperienceEnhanceRequest,
    InterviewQuestionsRequest,
    JobSummaryRequest,
    MatchingEnhanceRequest,
    ProfileEnhanceRequest,
    ProjectEnhanceRequest,
    ResumeGenerateRequest,
    ResumeImproveRequest,
    SkillsRecommendRequest,
)
from app.ai.schemas import AIResponse, GenerationMetadata, UsageMetrics


def _mock_response(content: str) -> AIResponse:
    return AIResponse(
        content=content,
        model="mock-model",
        provider="mock",
        usage=UsageMetrics(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        metadata=GenerationMetadata(model="mock-model", provider="mock", finish_reason="stop"),
    )


class _MockAIService:
    def __init__(self):
        self.generate_prompted = AsyncMock(return_value=_mock_response("Mock result"))
        self.generate = AsyncMock(return_value=_mock_response("Mock result"))


@pytest.fixture(autouse=True)
def _mock_ai_service():
    svc = _MockAIService()
    with patch("app.ai.features.resume.get_ai_service", return_value=svc), \
         patch("app.ai.features.cover_letter.get_ai_service", return_value=svc), \
         patch("app.ai.features.interview.get_ai_service", return_value=svc), \
         patch("app.ai.features.company_research.get_ai_service", return_value=svc), \
         patch("app.ai.features.email.get_ai_service", return_value=svc), \
         patch("app.ai.features.matching.get_ai_service", return_value=svc):
        yield svc


# ── Pydantic Request Schema Validation ──


class TestRequestSchemaValidation:
    def test_resume_generate_request_valid(self):
        req = ResumeGenerateRequest(profile_data="Senior developer")
        assert req.profile_data == "Senior developer"
        assert req.target_role == ""

    def test_resume_generate_request_empty_profile_fails(self):
        with pytest.raises(ValidationError):
            ResumeGenerateRequest(profile_data="")

    def test_resume_improve_request_valid(self):
        req = ResumeImproveRequest(current_content="Some content")
        assert req.section_type == "experience"

    def test_ats_optimize_request_valid(self):
        req = ATSOptimizeRequest(resume_content="Resume content")
        assert req.job_title == ""

    def test_ats_optimize_request_empty_resume_fails(self):
        with pytest.raises(ValidationError):
            ATSOptimizeRequest(resume_content="")

    def test_cover_letter_generate_request_valid(self):
        req = CoverLetterGenerateRequest(
            job_title="Engineer",
            company_name="Acme",
            job_description="desc",
            resume_text="resume",
        )
        assert req.tone.value == "professional"

    def test_cover_letter_generate_missing_fields_fails(self):
        with pytest.raises(ValidationError):
            CoverLetterGenerateRequest(job_title="Engineer")

    def test_cover_letter_assist_request_valid(self):
        req = CoverLetterAssistRequest(
            instruction="improve",
            content="My cover letter",
        )
        assert req.context == ""

    def test_interview_questions_request_valid(self):
        req = InterviewQuestionsRequest(job_title="Engineer", company="Google")
        assert req.count == 3

    def test_interview_questions_count_validation(self):
        with pytest.raises(ValidationError):
            InterviewQuestionsRequest(job_title="Engineer", company="Google", count=0)

    def test_application_questions_request_valid(self):
        req = ApplicationQuestionsRequest(job_title="Engineer", company="Acme")
        assert req.job_description == ""

    def test_company_research_request_valid(self):
        req = CompanyResearchRequest(company="Google")
        assert req.industry == ""

    def test_job_summary_request_valid(self):
        req = JobSummaryRequest(title="Engineer", company="Acme")
        assert req.description == ""

    def test_email_generate_request_valid(self):
        req = EmailGenerateRequest(email_type="follow_up")
        assert req.recipient == ""

    def test_email_type_enum_validation(self):
        with pytest.raises(ValidationError):
            EmailGenerateRequest(email_type="invalid_type")

    def test_matching_enhance_request_valid(self):
        req = MatchingEnhanceRequest(job_title="Engineer", company="Acme")
        assert req.current_score == 0.0

    def test_matching_score_range(self):
        with pytest.raises(ValidationError):
            MatchingEnhanceRequest(job_title="Engineer", company="Acme", current_score=150.0)

    def test_project_enhance_request_valid(self):
        req = ProjectEnhanceRequest(
            project_name="My Project",
            project_description="Description here",
        )
        assert req.target_role == ""

    def test_experience_enhance_request_valid(self):
        req = ExperienceEnhanceRequest(
            job_title="Engineer",
            company_name="Acme",
            current_description="Did things",
        )
        assert req.target_role == ""

    def test_skills_recommend_request_valid(self):
        req = SkillsRecommendRequest(current_skills="Python")
        assert req.industry == ""

    def test_profile_enhance_request_valid(self):
        req = ProfileEnhanceRequest(current_profile="My profile")
        assert req.improvement_areas == "summary, headline, skills, achievements"


# ── Resume AI Features ──


class TestResumeAIFeatures:
    async def test_ai_generate_resume(self):
        result = await ai_generate_resume(
            profile_data="Senior developer with 5 years experience",
            target_role="Tech Lead",
            target_company="Google",
        )
        assert "sections" in result
        assert result["provider"] == "mock"

    async def test_ai_generate_resume_defaults(self):
        result = await ai_generate_resume(profile_data="Entry level developer")
        assert result["sections"] == "Mock result"

    async def test_ai_improve_resume_section(self):
        result = await ai_improve_resume_section(
            section_type="experience",
            current_content="Worked on stuff",
            target_role="Senior Engineer",
        )
        assert "improved_content" in result

    async def test_ai_improve_resume_section_defaults(self):
        result = await ai_improve_resume_section(
            section_type="summary",
            current_content="Hard worker",
        )
        assert result["improved_content"] == "Mock result"

    async def test_ai_optimize_ats(self):
        result = await ai_optimize_ats(
            resume_content="My resume",
            job_title="Engineer",
            company="Acme",
            job_description="Do things",
        )
        assert "optimization" in result

    async def test_ai_optimize_ats_defaults(self):
        result = await ai_optimize_ats(resume_content="My resume")
        assert result["optimization"] == "Mock result"

    async def test_ai_enhance_profile(self):
        result = await ai_enhance_profile(
            current_profile="My profile",
            target_role="Director",
            industry="Tech",
        )
        assert "enhanced_profile" in result

    async def test_ai_enhance_profile_defaults(self):
        result = await ai_enhance_profile(current_profile="Basic profile")
        assert result["enhanced_profile"] == "Mock result"

    async def test_ai_recommend_skills(self):
        result = await ai_recommend_skills(
            current_skills="Python, JS",
            target_role="Full Stack",
            industry="SaaS",
            experience_level="Senior",
        )
        assert "recommendations" in result

    async def test_ai_recommend_skills_defaults(self):
        result = await ai_recommend_skills(current_skills="Python")
        assert result["recommendations"] == "Mock result"


# ── Project & Experience Enhancement (Sprint 3.1) ──


class TestProjectExperienceEnhancement:
    async def test_ai_enhance_project(self):
        result = await ai_enhance_project(
            project_name="AI Platform",
            project_description="Built an AI platform",
            target_role="ML Engineer",
            technologies="Python, TensorFlow",
        )
        assert "enhanced_description" in result
        assert result["provider"] == "mock"

    async def test_ai_enhance_project_defaults(self):
        result = await ai_enhance_project(
            project_name="CLI Tool",
            project_description="Command line tool",
        )
        assert result["enhanced_description"] == "Mock result"

    async def test_ai_enhance_experience(self):
        result = await ai_enhance_experience(
            job_title="Senior Engineer",
            company_name="Acme",
            current_description="Led a team",
            target_role="Director",
        )
        assert "improved_experience" in result
        assert result["provider"] == "mock"

    async def test_ai_enhance_experience_all_params(self):
        result = await ai_enhance_experience(
            job_title="Engineer",
            company_name="Google",
            current_description="Built features",
            target_role="Staff Engineer",
            target_company="Meta",
            date_range="2020-2023",
            job_context="High scale systems",
        )
        assert result["improved_experience"] == "Mock result"

    async def test_ai_enhance_profile_delegated(self):
        result = await ai_enhance_profile_delegated(
            current_profile="Full stack dev",
            target_role="Tech Lead",
            target_company="Google",
            experience_entries=[
                {"title": "Engineer", "company": "Acme", "description": "Built web apps"}
            ],
            project_entries=[
                {"name": "Dashboard", "description": "React dashboard", "technologies": "React"}
            ],
        )
        assert "enhanced_profile" in result
        assert "enhanced_experience" in result
        assert "enhanced_projects" in result

    async def test_ai_enhance_profile_delegated_no_entries(self):
        result = await ai_enhance_profile_delegated(
            current_profile="Dev",
            target_role="Senior",
        )
        assert "enhanced_profile" in result
        assert result["enhanced_experience"] is None
        assert result["enhanced_projects"] is None


# ── Cover Letter AI Features ──


class TestCoverLetterAIFeatures:
    async def test_ai_generate_cover_letter(self):
        result = await ai_generate_cover_letter(
            job_title="Software Engineer",
            company_name="Acme Inc",
            job_description="Build stuff",
            resume_text="I build stuff",
        )
        assert "cover_letter" in result
        assert result["provider"] == "mock"

    async def test_ai_generate_cover_letter_with_all_params(self):
        result = await ai_generate_cover_letter(
            job_title="Engineer",
            company_name="Acme",
            job_description="desc",
            resume_text="resume",
            tone="executive",
            style="classic",
            hiring_manager="Jane Doe",
        )
        assert result["cover_letter"] == "Mock result"

    async def test_ai_assist_cover_letter(self):
        result = await ai_assist_cover_letter(
            content="My cover letter",
            instruction="make it more professional",
        )
        assert "edited_content" in result

    async def test_ai_assist_cover_letter_with_context(self):
        result = await ai_assist_cover_letter(
            content="My letter",
            instruction="shorten",
            context="Targeting Google",
        )
        assert result["edited_content"] == "Mock result"


# ── Interview AI Features ──


class TestInterviewAIFeatures:
    async def test_ai_generate_interview_questions(self):
        result = await ai_generate_interview_questions(
            job_title="Engineer",
            company="Google",
            job_description="Build things",
        )
        assert "questions" in result

    async def test_ai_generate_interview_questions_all_params(self):
        result = await ai_generate_interview_questions(
            job_title="SRE",
            company="Netflix",
            job_description="Run prod",
            background="5 years ops",
            question_types="technical, behavioral",
            interview_round="onsite",
            count=5,
        )
        assert result["questions"] == "Mock result"

    async def test_ai_answer_application_questions(self):
        result = await ai_answer_application_questions(
            job_title="Engineer",
            company="Acme",
            job_description="desc",
            profile_summary="summary",
            questions="Why you?",
        )
        assert "answers" in result

    async def test_ai_answer_application_questions_minimal(self):
        result = await ai_answer_application_questions(
            job_title="Engineer",
            company="Acme",
        )
        assert result["answers"] == "Mock result"


# ── Company Research AI Features ──


class TestCompanyResearchAIFeatures:
    async def test_ai_company_research(self):
        result = await ai_company_research(
            company="Google",
            industry="Tech",
            role="Engineer",
        )
        assert "research" in result

    async def test_ai_company_research_defaults(self):
        result = await ai_company_research(company="Acme")
        assert result["research"] == "Mock result"

    async def test_ai_job_summary(self):
        result = await ai_job_summary(
            title="Engineer",
            company="Acme",
            description="desc",
        )
        assert "summary" in result

    async def test_ai_job_summary_all_params(self):
        result = await ai_job_summary(
            title="Senior Engineer",
            company="Google",
            description="Build systems",
            requirements="5 years exp",
            preferred_qualifications="Kubernetes",
            profile_summary="I know k8s",
        )
        assert result["summary"] == "Mock result"


# ── Email AI Features ──


class TestEmailAIFeatures:
    async def test_ai_generate_email(self):
        result = await ai_generate_email(
            email_type="follow-up",
            recipient="John",
            company="Acme",
            job_title="Engineer",
        )
        assert "email" in result

    async def test_ai_generate_email_all_params(self):
        result = await ai_generate_email(
            email_type="application",
            recipient="Jane Doe",
            recipient_title="Hiring Manager",
            company="Google",
            your_name="Bob",
            job_title="SDE",
            context="Referred by friend",
        )
        assert result["email"] == "Mock result"

    async def test_ai_generate_email_minimal(self):
        result = await ai_generate_email(email_type="networking")
        assert result["email"] == "Mock result"


# ── Matching AI Feature (Registry check) ──


class TestMatchingAIFeatures:
    async def test_ai_enhance_matching(self):
        result = await ai_enhance_matching(
            job_title="Engineer",
            company="Acme",
            job_description="desc",
            profile_skills="Python",
            profile_experience="5 years",
            profile_education="BS CS",
        )
        assert "analysis" in result

    async def test_ai_enhance_matching_minimal(self):
        result = await ai_enhance_matching(
            job_title="Engineer",
            company="Acme",
        )
        assert result["analysis"] == "Mock result"

    async def test_ai_enhance_matching_uses_registry(self):
        svc = _MockAIService()
        with patch("app.ai.features.matching.get_ai_service", return_value=svc):
            await ai_enhance_matching(job_title="Engineer", company="Acme")
            svc.generate_prompted.assert_called_once()
            call_kwargs = svc.generate_prompted.call_args.kwargs
            assert call_kwargs["template_name"] == "matching-analysis-ai"
            assert "job_title" in call_kwargs["variables"]


# ── Prompt Registry Validation ──


class TestPromptRegistryFeatureNames:
    def test_all_feature_templates_registered(self):
        from app.ai.dependencies import get_prompt_registry
        registry = get_prompt_registry()
        names = registry.list_names()
        required = [
            "resume-ai-generation",
            "resume-improvement-ai",
            "ats-optimization-ai",
            "profile-enhancement-ai",
            "skill-recommendations-ai",
            "interview-questions-ai",
            "application-questions-ai",
            "company-research-ai",
            "job-summary-ai",
            "email-generation",
            "cover-letter-ai",
            "cover-letter-ai-assist",
            "matching-analysis-ai",
            "project-enhancement-ai",
            "experience-enhancement-ai",
        ]
        for name in required:
            assert name in names, f"Sprint 3 template '{name}' missing from registry"

    def test_legacy_templates_preserved(self):
        from app.ai.dependencies import get_prompt_registry
        registry = get_prompt_registry()
        names = registry.list_names()
        legacy = [
            "resume-generation",
            "cover-letter",
            "resume-improvement",
            "interview-questions",
            "company-research",
            "job-summary",
            "profile-enhancement",
            "skill-suggestions",
            "application-questions",
            "ats-optimization",
        ]
        for name in legacy:
            assert name in names, f"Legacy template '{name}' missing from registry"


# ── Features Package Exports ──


class TestFeaturesPackageExports:
    def test_all_features_exported(self):
        from app.ai import features
        expected = [
            "ai_generate_resume",
            "ai_improve_resume_section",
            "ai_optimize_ats",
            "ai_enhance_profile",
            "ai_enhance_profile_delegated",
            "ai_enhance_project",
            "ai_enhance_experience",
            "ai_recommend_skills",
            "ai_generate_cover_letter",
            "ai_assist_cover_letter",
            "ai_generate_interview_questions",
            "ai_answer_application_questions",
            "ai_company_research",
            "ai_job_summary",
            "ai_generate_email",
            "ai_enhance_matching",
        ]
        for name in expected:
            assert hasattr(features, name), f"{name} not exported from features package"

    def test_import_from_package(self):
        from app.ai.features import ai_generate_resume, ai_enhance_project, ai_enhance_experience
        assert callable(ai_generate_resume)
        assert callable(ai_enhance_project)
        assert callable(ai_enhance_experience)


# ── API Endpoint Tests ──


@pytest.fixture
def app():
    import uuid
    from fastapi import FastAPI
    from app.api.v1.ai_features import router
    from app.api.deps import get_current_user
    from app.api.responses import handle_app_error
    from app.core.exceptions import AppError, AuthenticationError, AuthorizationError, ConflictError, NotFoundError, ValidationError

    class MockUser:
        id = uuid.uuid4()
        is_active = True
        email = "test@example.com"
        first_name = "Test"
        last_name = "User"

    application = FastAPI()
    application.add_exception_handler(AppError, handle_app_error)
    application.add_exception_handler(NotFoundError, handle_app_error)
    application.add_exception_handler(ValidationError, handle_app_error)
    application.add_exception_handler(AuthenticationError, handle_app_error)
    application.add_exception_handler(AuthorizationError, handle_app_error)
    application.add_exception_handler(ConflictError, handle_app_error)
    application.include_router(router, prefix="/ai")
    application.dependency_overrides[get_current_user] = lambda: MockUser()
    return application


@pytest.fixture
async def client(app):
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestFeaturesAPIEndpoints:
    async def test_resume_generate_endpoint(self, client):
        response = await client.post("/ai/resume/generate", json={
            "profile_data": "Senior developer",
            "target_role": "Tech Lead",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sections" in data["data"]

    async def test_resume_improve_endpoint(self, client):
        response = await client.post("/ai/resume/improve", json={
            "section_type": "experience",
            "current_content": "Did stuff",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "improved_content" in data["data"]

    async def test_resume_ats_optimize_endpoint(self, client):
        response = await client.post("/ai/resume/ats-optimize", json={
            "resume_content": "My resume",
            "job_title": "Engineer",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "optimization" in data["data"]

    async def test_profile_enhance_endpoint(self, client):
        response = await client.post("/ai/profile/enhance", json={
            "current_profile": "My profile",
            "target_role": "Director",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "enhanced_profile" in data["data"]

    async def test_profile_skills_recommend_endpoint(self, client):
        response = await client.post("/ai/profile/skills-recommend", json={
            "current_skills": "Python",
            "target_role": "Full Stack",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "recommendations" in data["data"]

    async def test_project_enhance_endpoint(self, client):
        response = await client.post("/ai/resume/project-enhance", json={
            "project_name": "AI Platform",
            "project_description": "Built an AI platform",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "enhanced_description" in data["data"]

    async def test_experience_enhance_endpoint(self, client):
        response = await client.post("/ai/resume/experience-enhance", json={
            "job_title": "Engineer",
            "company_name": "Acme",
            "current_description": "Did things",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "improved_experience" in data["data"]

    async def test_interview_questions_endpoint(self, client):
        response = await client.post("/ai/interview/questions", json={
            "job_title": "Engineer",
            "company": "Google",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "questions" in data["data"]

    async def test_application_questions_endpoint(self, client):
        response = await client.post("/ai/interview/application-questions", json={
            "job_title": "Engineer",
            "company": "Acme",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "answers" in data["data"]

    async def test_company_research_endpoint(self, client):
        response = await client.post("/ai/company/research", json={
            "company": "Google",
            "industry": "Tech",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "research" in data["data"]

    async def test_job_summarize_endpoint(self, client):
        response = await client.post("/ai/job/summarize", json={
            "title": "Engineer",
            "company": "Acme",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "summary" in data["data"]

    async def test_email_generate_endpoint(self, client):
        response = await client.post("/ai/email/generate", json={
            "email_type": "follow_up",
            "recipient": "John",
            "company": "Acme",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "email" in data["data"]

    async def test_matching_enhance_endpoint(self, client):
        response = await client.post("/ai/matching/enhance", json={
            "job_title": "Engineer",
            "company": "Acme",
            "job_description": "desc",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data["data"]

    async def test_cover_letter_generate_endpoint(self, client):
        response = await client.post("/ai/cover-letter/generate", json={
            "job_title": "Engineer",
            "company_name": "Acme",
            "job_description": "desc",
            "resume_text": "resume",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cover_letter" in data["data"]

    async def test_cover_letter_assist_endpoint(self, client):
        response = await client.post("/ai/cover-letter/assist", json={
            "instruction": "improve",
            "content": "My cover letter",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "edited_content" in data["data"]

    async def test_pydantic_validation_on_endpoint(self, client):
        response = await client.post("/ai/resume/generate", json={})
        assert response.status_code == 422

    async def test_email_type_validation_on_endpoint(self, client):
        response = await client.post("/ai/email/generate", json={"email_type": "not_a_type"})
        assert response.status_code == 422
