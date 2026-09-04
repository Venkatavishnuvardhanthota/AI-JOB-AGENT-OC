from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToneEnum(str, Enum):
    professional = "professional"
    technical = "technical"
    executive = "executive"
    friendly = "friendly"
    concise = "concise"
    graduate = "graduate"
    career_change = "career_change"


class StyleEnum(str, Enum):
    modern = "modern"
    classic = "classic"
    creative = "creative"


class EmailTypeEnum(str, Enum):
    recruiter_outreach = "recruiter_outreach"
    follow_up = "follow_up"
    thank_you = "thank_you"
    application = "application"
    networking = "networking"
    referral_request = "referral_request"
    acceptance = "acceptance"
    negotiation = "negotiation"
    rejection = "rejection"


class InterviewRoundEnum(str, Enum):
    first = "first"
    second = "second"
    final = "final"
    onsite = "onsite"
    technical = "technical"
    phone = "phone"


class QuestionTypeEnum(str, Enum):
    behavioral = "behavioral"
    technical = "technical"
    culture = "culture"
    scenario = "scenario"
    all = "all"


# ── Resume Feature Schemas ──


class ResumeGenerateRequest(BaseModel):
    profile_data: str = Field(min_length=1, max_length=50000, description="Career profile data to generate resume from")
    target_role: str = Field(default="", max_length=200, description="Target job role")
    target_company: str = Field(default="", max_length=200, description="Target company")
    section_types: list[str] | None = Field(default=None, description="Specific sections to generate")


class ResumeImproveRequest(BaseModel):
    section_type: str = Field(default="experience", max_length=100, description="Type of section to improve")
    current_content: str = Field(min_length=1, max_length=10000, description="Current section content")
    target_role: str = Field(default="", max_length=200, description="Target job role")
    target_company: str = Field(default="", max_length=200, description="Target company")
    job_context: str = Field(default="", max_length=5000, description="Job description context")
    improvement_areas: str = Field(default="grammar, tone, action_verbs, keywords", max_length=500)


class ATSOptimizeRequest(BaseModel):
    resume_content: str = Field(min_length=1, max_length=20000, description="Full resume content")
    job_title: str = Field(default="", max_length=200, description="Target job title")
    company: str = Field(default="", max_length=200, description="Target company")
    job_description: str = Field(default="", max_length=10000, description="Job description for keyword matching")


class ProfileEnhanceRequest(BaseModel):
    current_profile: str = Field(min_length=1, max_length=10000, description="Current profile content")
    target_role: str = Field(default="", max_length=200, description="Target job role")
    industry: str = Field(default="", max_length=200, description="Industry context")
    improvement_areas: str = Field(default="summary, headline, skills, achievements", max_length=500)
    target_company: str = Field(default="", max_length=200, description="Target company")
    experience_entries: list[dict] | None = Field(
        default=None, description="Experience entries for targeted enhancement"
    )
    project_entries: list[dict] | None = Field(default=None, description="Project entries for targeted enhancement")


class SkillsRecommendRequest(BaseModel):
    current_skills: str = Field(min_length=1, max_length=5000, description="Current skills")
    target_role: str = Field(default="", max_length=200, description="Target job role")
    industry: str = Field(default="", max_length=200, description="Industry")
    experience_level: str = Field(default="", max_length=100, description="Experience level")
    job_market_context: str = Field(default="", max_length=2000, description="Job market context")


class ProjectEnhanceRequest(BaseModel):
    project_name: str = Field(min_length=1, max_length=200, description="Project name")
    project_description: str = Field(min_length=1, max_length=5000, description="Current project description")
    target_role: str = Field(default="", max_length=200, description="Target job role")
    target_company: str = Field(default="", max_length=200, description="Target company")
    technologies: str = Field(default="", max_length=2000, description="Technologies used")
    job_context: str = Field(default="", max_length=5000, description="Job context")


class ExperienceEnhanceRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=200, description="Job title")
    company_name: str = Field(min_length=1, max_length=200, description="Company name")
    current_description: str = Field(min_length=1, max_length=10000, description="Current experience description")
    target_role: str = Field(default="", max_length=200, description="Target job role")
    target_company: str = Field(default="", max_length=200, description="Target company")
    date_range: str = Field(default="", max_length=100, description="Employment date range")
    job_context: str = Field(default="", max_length=5000, description="Job context")


# ── Cover Letter Feature Schemas ──


class CoverLetterGenerateRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=200, description="Job title")
    company_name: str = Field(min_length=1, max_length=200, description="Company name")
    job_description: str = Field(min_length=1, max_length=10000, description="Job description")
    resume_text: str = Field(min_length=1, max_length=20000, description="Resume content")
    tone: ToneEnum = Field(default=ToneEnum.professional, description="Writing tone")
    style: StyleEnum = Field(default=StyleEnum.modern, description="Cover letter style")
    hiring_manager: str = Field(default="", max_length=200, description="Hiring manager name")


class CoverLetterAssistRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=500, description="Edit instruction")
    content: str = Field(min_length=1, max_length=10000, description="Current cover letter content")
    context: str = Field(default="", max_length=2000, description="Additional context")


# ── Interview Feature Schemas ──


class InterviewQuestionsRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=200, description="Job title")
    company: str = Field(min_length=1, max_length=200, description="Company name")
    job_description: str = Field(default="", max_length=10000, description="Job description")
    background: str = Field(default="", max_length=5000, description="Candidate background")
    question_types: str = Field(
        default="behavioral, technical, culture", max_length=200, description="Types of questions"
    )
    interview_round: InterviewRoundEnum = Field(default=InterviewRoundEnum.first, description="Interview round")
    count: int = Field(default=3, ge=1, le=20, description="Number of questions per type")


class ApplicationQuestionsRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=200, description="Job title")
    company: str = Field(min_length=1, max_length=200, description="Company name")
    job_description: str = Field(default="", max_length=10000, description="Job description")
    profile_summary: str = Field(default="", max_length=5000, description="Profile summary")
    questions: str = Field(default="", max_length=10000, description="Questions to answer")


# ── Company Research Feature Schemas ──


class CompanyResearchRequest(BaseModel):
    company: str = Field(min_length=1, max_length=200, description="Company name")
    industry: str = Field(default="", max_length=200, description="Industry")
    role: str = Field(default="", max_length=200, description="Target role")
    company_url: str = Field(default="", max_length=500, description="Company URL")


class JobSummaryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200, description="Job title")
    company: str = Field(min_length=1, max_length=200, description="Company name")
    description: str = Field(default="", max_length=20000, description="Job description")
    requirements: str = Field(default="", max_length=10000, description="Job requirements")
    preferred_qualifications: str = Field(default="", max_length=10000, description="Preferred qualifications")
    profile_summary: str = Field(default="", max_length=5000, description="Candidate profile summary")


# ── Email Feature Schemas ──


class EmailGenerateRequest(BaseModel):
    email_type: EmailTypeEnum = Field(description="Type of email to generate")
    recipient: str = Field(default="", max_length=200, description="Recipient name")
    recipient_title: str = Field(default="", max_length=200, description="Recipient job title")
    company: str = Field(default="", max_length=200, description="Company name")
    your_name: str = Field(default="", max_length=200, description="Sender name")
    job_title: str = Field(default="", max_length=200, description="Job title")
    context: str = Field(default="", max_length=2000, description="Additional context")


# ── Matching Feature Schemas ──


class MatchingEnhanceRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=200, description="Job title")
    company: str = Field(min_length=1, max_length=200, description="Company name")
    job_description: str = Field(default="", max_length=10000, description="Job description")
    profile_skills: str = Field(default="", max_length=5000, description="Candidate skills")
    profile_experience: str = Field(default="", max_length=10000, description="Candidate experience")
    profile_education: str = Field(default="", max_length=5000, description="Candidate education")
    current_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Current match score")


# ── Response Models ──


class AIFeatureResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]


class AIFeatureError(BaseModel):
    success: bool = False
    error: str
    code: str | None = None
