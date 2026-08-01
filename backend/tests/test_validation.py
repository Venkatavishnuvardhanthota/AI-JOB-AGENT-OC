"""Pydantic validation tests — boundary conditions, missing fields, wrong types, enums, large payloads."""

import pytest
from pydantic import ValidationError

from app.ai.features.schemas import (
    ApplicationQuestionsRequest,
    ATSOptimizeRequest,
    CompanyResearchRequest,
    CoverLetterAssistRequest,
    CoverLetterGenerateRequest,
    EmailGenerateRequest,
    EmailTypeEnum,
    InterviewQuestionsRequest,
    MatchingEnhanceRequest,
    ResumeGenerateRequest,
)
from app.ai.schemas import AIRequest, AIUpdateConfig


class TestResumeGenerateRequest:
    def test_valid(self):
        r = ResumeGenerateRequest(profile_data="data", target_role="Engineer")
        assert r.profile_data == "data"
        assert r.target_role == "Engineer"

    def test_optional_target_role(self):
        r = ResumeGenerateRequest(profile_data="data")
        assert r.profile_data == "data"

    def test_missing_profile_data_fails(self):
        with pytest.raises(ValidationError):
            ResumeGenerateRequest()

    def test_empty_profile_data_fails(self):
        with pytest.raises(ValidationError):
            ResumeGenerateRequest(profile_data="", target_role="Engineer")

    def test_max_length_profile_data_accepted(self):
        r = ResumeGenerateRequest(profile_data="x" * 50000)
        assert len(r.profile_data) == 50000

    def test_oob_profile_data_fails(self):
        with pytest.raises(ValidationError):
            ResumeGenerateRequest(profile_data="x" * 50001)

    def test_oob_target_role_fails(self):
        with pytest.raises(ValidationError):
            ResumeGenerateRequest(profile_data="data", target_role="x" * 201)


class TestCoverLetterGenerateRequest:
    def test_valid(self):
        r = CoverLetterGenerateRequest(job_title="Eng", company_name="Acme", job_description="desc", resume_text="resume")
        assert r.job_title == "Eng"

    def test_missing_fields_fails(self):
        with pytest.raises(ValidationError):
            CoverLetterGenerateRequest(job_title="Eng")

    def test_empty_fields_fails(self):
        with pytest.raises(ValidationError):
            CoverLetterGenerateRequest(job_title="", company_name="", job_description="", resume_text="")

    def test_tone_enum_default(self):
        r = CoverLetterGenerateRequest(job_title="Eng", company_name="Acme", job_description="desc", resume_text="resume")
        assert r.tone.value == "professional"

    def test_style_enum_default(self):
        r = CoverLetterGenerateRequest(job_title="Eng", company_name="Acme", job_description="desc", resume_text="resume")
        assert r.style.value == "modern"

    def test_invalid_tone_fails(self):
        with pytest.raises(ValidationError):
            CoverLetterGenerateRequest(job_title="Eng", company_name="Acme", job_description="desc", resume_text="resume", tone="invalid_tone")


class TestCoverLetterAssistRequest:
    def test_valid(self):
        r = CoverLetterAssistRequest(instruction="improve", content="My letter")
        assert r.instruction == "improve"

    def test_empty_instruction_fails(self):
        with pytest.raises(ValidationError):
            CoverLetterAssistRequest(instruction="", content="letter")

    def test_missing_content_fails(self):
        with pytest.raises(ValidationError):
            CoverLetterAssistRequest(instruction="improve")


class TestEmailGenerateRequest:
    def test_valid(self):
        r = EmailGenerateRequest(email_type="follow_up", recipient="John", company="Acme")
        assert r.email_type == EmailTypeEnum.follow_up

    def test_invalid_email_type_fails(self):
        with pytest.raises(ValidationError):
            EmailGenerateRequest(email_type="not_a_type", recipient="John", company="Acme")

    def test_empty_recipient_is_ok(self):
        r = EmailGenerateRequest(email_type="follow_up", recipient="", company="Acme")
        assert r.recipient == ""

    def test_valid_email_types(self):
        for etype in EmailTypeEnum:
            r = EmailGenerateRequest(email_type=etype.value, recipient="John", company="Acme")
            assert r.email_type == etype


class TestInterviewQuestionsRequest:
    def test_valid(self):
        r = InterviewQuestionsRequest(job_title="Eng", company="Google")
        assert r.job_title == "Eng"

    def test_optional_count(self):
        r = InterviewQuestionsRequest(job_title="Eng", company="Google", count=10)
        assert r.count == 10

    def test_zero_count_fails(self):
        with pytest.raises(ValidationError):
            InterviewQuestionsRequest(job_title="Eng", company="Google", count=0)

    def test_negative_count_fails(self):
        with pytest.raises(ValidationError):
            InterviewQuestionsRequest(job_title="Eng", company="Google", count=-1)

    def test_oob_count_fails(self):
        with pytest.raises(ValidationError):
            InterviewQuestionsRequest(job_title="Eng", company="Google", count=21)

    def test_interview_round_default(self):
        r = InterviewQuestionsRequest(job_title="Eng", company="Google")
        assert r.interview_round.value == "first"


class TestCompanyResearchRequest:
    def test_valid(self):
        r = CompanyResearchRequest(company="Google")
        assert r.company == "Google"

    def test_optional_industry(self):
        r = CompanyResearchRequest(company="Google")
        assert r.industry == ""

    def test_missing_company_fails(self):
        with pytest.raises(ValidationError):
            CompanyResearchRequest()


class TestMatchingEnhanceRequest:
    def test_valid(self):
        r = MatchingEnhanceRequest(job_title="Eng", company="Acme", job_description="desc")
        assert r.job_title == "Eng"

    def test_optional_profile_fields(self):
        r = MatchingEnhanceRequest(job_title="Eng", company="Acme")
        assert r.job_description == ""

    def test_current_score_default(self):
        r = MatchingEnhanceRequest(job_title="Eng", company="Acme", job_description="desc")
        assert r.current_score == 0.0

    def test_negative_score_fails(self):
        with pytest.raises(ValidationError):
            MatchingEnhanceRequest(job_title="Eng", company="Acme", job_description="desc", current_score=-1)

    def test_oob_score_fails(self):
        with pytest.raises(ValidationError):
            MatchingEnhanceRequest(job_title="Eng", company="Acme", job_description="desc", current_score=100.1)


class TestATSAdaptRequest:
    def test_valid(self):
        r = ATSOptimizeRequest(resume_content="resume")
        assert r.resume_content == "resume"

    def test_empty_resume_content_fails(self):
        with pytest.raises(ValidationError):
            ATSOptimizeRequest(resume_content="")

    def test_optional_job_fields(self):
        r = ATSOptimizeRequest(resume_content="resume")
        assert r.job_title == ""


class TestApplicationQuestionsRequest:
    def test_valid(self):
        r = ApplicationQuestionsRequest(job_title="Eng", company="Acme")
        assert r.job_title == "Eng"


class TestAIRequest:
    def test_valid_minimal(self):
        r = AIRequest(prompt="Hello")
        assert r.prompt == "Hello"

    def test_empty_prompt_fails(self):
        with pytest.raises(ValidationError):
            AIRequest(prompt="")

    def test_valid_full(self):
        r = AIRequest(prompt="Hello", system_prompt="Be helpful", model="gpt-4", temperature=0.5, max_tokens=100, provider="openai")
        assert r.provider == "openai"


class TestAIUpdateConfig:
    def test_valid(self):
        r = AIUpdateConfig(default_provider="openai", temperature=0.7)
        assert r.default_provider == "openai"

    def test_all_fields_none(self):
        r = AIUpdateConfig()
        assert r.default_provider is None

    def test_invalid_temperature_negative_fails(self):
        with pytest.raises(ValidationError):
            AIUpdateConfig(temperature=-0.1)

    def test_invalid_temperature_over_2_fails(self):
        with pytest.raises(ValidationError):
            AIUpdateConfig(temperature=2.5)
