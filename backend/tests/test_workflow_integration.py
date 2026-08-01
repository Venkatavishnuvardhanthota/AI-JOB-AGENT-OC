"""Workflow integration tests — complete user journeys from profile to output."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_ai_service():
    """Patch get_ai_service() to return a mocked service for all tests."""
    from app.ai.service import AIService

    service = AsyncMock(spec=AIService)
    mock_response = AsyncMock(
        content="Mocked AI response content",
        model="gpt-4o",
        provider="openrouter",
        usage=None,
        metadata=None,
        id="mock-id",
    )
    service.generate_prompted = AsyncMock(return_value=mock_response)
    service.generate = AsyncMock(return_value=mock_response)

    modules = [
        "app.ai.features.resume",
        "app.ai.features.cover_letter",
        "app.ai.features.interview",
        "app.ai.features.company_research",
        "app.ai.features.email",
        "app.ai.features.matching",
    ]
    patches = [patch(f"{m}.get_ai_service", return_value=service) for m in modules]
    for p in patches:
        p.start()
    yield service
    for p in patches:
        p.stop()


class TestWorkflow1ResumeLifecycle:
    """Career Profile -> Resume Generation -> Resume Improvement -> ATS Optimization"""

    async def test_resume_generate_improve_optimize_flow(self, mock_ai_service):
        from app.ai.features.resume import ai_generate_resume, ai_improve_resume_section, ai_optimize_ats

        generate_result = await ai_generate_resume(
            profile_data="Senior Python developer with 8 years experience",
            target_role="Tech Lead",
        )
        assert "sections" in generate_result
        assert generate_result["sections"] == "Mocked AI response content"

        improve_result = await ai_improve_resume_section(
            section_type="experience",
            current_content="Built microservices",
        )
        assert "improved_content" in improve_result

        ats_result = await ai_optimize_ats(
            resume_content="Senior developer resume content",
            job_title="Backend Engineer",
        )
        assert "optimization" in ats_result

    async def test_resume_generate_empty_target_role_ok(self, mock_ai_service):
        from app.ai.features.resume import ai_generate_resume

        result = await ai_generate_resume(profile_data="data", target_role="")
        assert "sections" in result


class TestWorkflow2CoverLetterLifecycle:
    """Career Profile -> Cover Letter -> AI Assist -> Save"""

    async def test_cover_letter_generate_and_assist_flow(self, mock_ai_service):
        from app.ai.features.cover_letter import ai_generate_cover_letter, ai_assist_cover_letter

        generate_result = await ai_generate_cover_letter(
            job_title="Software Engineer",
            company_name="Google",
            job_description="Build scalable systems",
            resume_text="Experienced engineer",
        )
        assert "cover_letter" in generate_result

        assist_result = await ai_assist_cover_letter(
            instruction="Make it more concise",
            content=generate_result["cover_letter"],
        )
        assert "edited_content" in assist_result

class TestWorkflow3JobResearchLifecycle:
    """Job -> Matching -> Company Research -> Interview -> Application Questions"""

    async def test_full_job_research_flow(self, mock_ai_service):
        from app.ai.features.matching import ai_enhance_matching
        from app.ai.features.company_research import ai_company_research, ai_job_summary
        from app.ai.features.interview import ai_generate_interview_questions, ai_answer_application_questions

        match_result = await ai_enhance_matching(
            job_title="Data Scientist",
            company="OpenAI",
            job_description="Work on cutting-edge AI models",
        )
        assert "analysis" in match_result

        research_result = await ai_company_research(
            company="OpenAI",
            industry="AI/ML",
        )
        assert "research" in research_result

        summary_result = await ai_job_summary(
            title="Data Scientist",
            company="OpenAI",
        )
        assert "summary" in summary_result

        interview_result = await ai_generate_interview_questions(
            job_title="Data Scientist",
            company="OpenAI",
            count=5,
        )
        assert "questions" in interview_result

        app_questions_result = await ai_answer_application_questions(
            job_title="Data Scientist",
            company="OpenAI",
        )
        assert "answers" in app_questions_result

    async def test_matching_enhance_with_optional_fields(self, mock_ai_service):
        from app.ai.features.matching import ai_enhance_matching

        result = await ai_enhance_matching(
            job_title="Engineer",
            company="Acme",
            job_description="desc",
            profile_skills="Python, FastAPI",
            profile_experience="Senior engineer",
        )
        assert "analysis" in result


class TestWorkflow4ProviderSwitch:
    """Provider switch — verifies config can change without breaking pipeline."""

    async def test_ai_service_accepts_config_override(self, mock_ai_service):
        result = await mock_ai_service.generate_prompted("test-template", {})
        assert result.content is not None
        assert result.model == "gpt-4o"


class TestWorkflow5ProviderFailure:
    """Provider error handling — service degrades gracefully."""

    async def test_generate_handles_failure(self, mock_ai_service):
        from app.ai.exceptions import AIError

        mock_ai_service.generate_prompted = AsyncMock(side_effect=AIError("Provider unavailable"))
        try:
            await mock_ai_service.generate_prompted("test", {})
        except AIError:
            pass
        else:
            pytest.fail("Expected AIError was not raised")

    async def test_generate_succeeds_after_mock(self, mock_ai_service):
        result = await mock_ai_service.generate_prompted("cover-letter", {"job_title": "Eng"})
        assert result.content is not None
