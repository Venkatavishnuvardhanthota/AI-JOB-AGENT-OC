from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import structlog

from app.ai.config import AIConfig
from app.ai.prompts.registry import PromptTemplateRegistry
from app.ai.registry import AIProviderRegistry
from app.ai.service import AIService

logger = structlog.get_logger(__name__)

_config_store: dict[str, Any] = {"config": None, "revision": 0}
_registered_revision: int = -1


@lru_cache
def _get_registry() -> AIProviderRegistry:
    return AIProviderRegistry()


def _build_env_config() -> AIConfig:
    from app.core.config import settings

    provider_params: dict[str, dict[str, Any]] = {}
    for name, key_attr, url_attr, model_attr in [
        ("openrouter", "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "OPENROUTER_DEFAULT_MODEL"),
        ("openai", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_DEFAULT_MODEL"),
        ("anthropic", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_DEFAULT_MODEL"),
        ("gemini", "GEMINI_API_KEY", "GEMINI_BASE_URL", "GEMINI_DEFAULT_MODEL"),
        ("ollama", None, "OLLAMA_BASE_URL", "OLLAMA_DEFAULT_MODEL"),
    ]:
        params: dict[str, Any] = {}
        if key_attr and getattr(settings, key_attr, None):
            params["api_key"] = getattr(settings, key_attr)
        if url_attr:
            params["base_url"] = getattr(settings, url_attr)
        params["default_model"] = getattr(settings, model_attr)
        provider_params[name] = params

    return AIConfig(
        default_provider=settings.AI_DEFAULT_PROVIDER,
        default_model=settings.AI_DEFAULT_MODEL,
        fallback_model=settings.AI_FALLBACK_MODEL,
        fallback_provider=settings.AI_FALLBACK_PROVIDER or None,
        max_retries=settings.AI_MAX_RETRIES,
        retry_delay_seconds=settings.AI_RETRY_DELAY_SECONDS,
        timeout_seconds=settings.AI_TIMEOUT_SECONDS,
        temperature=settings.AI_TEMPERATURE,
        max_tokens=settings.AI_MAX_TOKENS,
        enabled_providers=settings.AI_ENABLED_PROVIDERS_LIST,
        streaming_enabled=settings.AI_STREAMING_ENABLED,
        openrouter_api_key=settings.OPENROUTER_API_KEY,
        openrouter_base_url=settings.OPENROUTER_BASE_URL,
        openrouter_default_model=settings.OPENROUTER_DEFAULT_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
        openai_base_url=settings.OPENAI_BASE_URL,
        openai_default_model=settings.OPENAI_DEFAULT_MODEL,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        anthropic_base_url=settings.ANTHROPIC_BASE_URL,
        anthropic_default_model=settings.ANTHROPIC_DEFAULT_MODEL,
        gemini_api_key=settings.GEMINI_API_KEY,
        gemini_base_url=settings.GEMINI_BASE_URL,
        gemini_default_model=settings.GEMINI_DEFAULT_MODEL,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        ollama_default_model=settings.OLLAMA_DEFAULT_MODEL,
        provider_params=provider_params,
    )


async def build_config_from_db(db: Any) -> AIConfig:
    """Build AIConfig by merging environment defaults with persisted settings."""
    from database.repositories.ai_settings import AISettingsRepository
    from database.repositories.provider_configuration import ProviderConfigurationRepository

    config = _build_env_config()
    ai_settings_repo = AISettingsRepository(db)
    provider_config_repo = ProviderConfigurationRepository(db)

    saved = await ai_settings_repo.get()
    if saved is not None:
        enabled = (
            [p.strip() for p in (saved.enabled_providers or "").split(",") if p.strip()]
            or config.enabled_providers
        )
        config = config.model_copy(
            update={
                "default_provider": saved.default_provider or config.default_provider,
                "default_model": saved.default_model or config.default_model,
                "fallback_provider": saved.fallback_provider or config.fallback_provider,
                "fallback_model": saved.fallback_model or config.fallback_model,
                "temperature": saved.temperature if saved.temperature is not None else config.temperature,
                "max_tokens": saved.max_tokens if saved.max_tokens is not None else config.max_tokens,
                "timeout_seconds": saved.timeout_seconds or config.timeout_seconds,
                "max_retries": saved.max_retries if saved.max_retries is not None else config.max_retries,
                "retry_delay_seconds": (
                    saved.retry_delay_seconds if saved.retry_delay_seconds is not None else config.retry_delay_seconds
                ),
                "streaming_enabled": (
                    saved.streaming_enabled if saved.streaming_enabled is not None else config.streaming_enabled
                ),
                "enabled_providers": enabled,
            }
        )

    saved_providers = await provider_config_repo.list_by_type("ai")
    params: dict[str, dict[str, Any]] = {k: dict(v) for k, v in config.provider_params.items()}
    for row in saved_providers:
        existing = dict(params.get(row.provider_name) or {})
        if row.api_key:
            existing["api_key"] = row.api_key
        if row.api_url:
            existing["base_url"] = row.api_url
        if row.default_model:
            existing["default_model"] = row.default_model
        existing["enabled"] = bool(row.is_enabled)
        if row.config:
            try:
                extra = json.loads(row.config)
            except (TypeError, ValueError):
                extra = {}
            for key in (
                "temperature",
                "max_tokens",
                "timeout_seconds",
                "max_retries",
                "retry_delay_seconds",
                "streaming_enabled",
            ):
                if extra.get(key) is not None:
                    existing[key] = extra[key]
        params[row.provider_name] = existing

    enabled_set = set(config.enabled_providers)
    for name, p in params.items():
        if p.get("enabled") is False:
            enabled_set.discard(name)
        elif p.get("enabled") is True:
            enabled_set.add(name)

    return config.model_copy(
        update={
            "provider_params": params,
            "enabled_providers": sorted(enabled_set),
        }
    )


async def apply_config(db: Any) -> AIConfig:
    """Reload the persisted AI configuration and invalidate registered providers."""
    global _registered_revision
    try:
        config = await build_config_from_db(db)
    except Exception:
        logger.exception("Failed to load persisted AI config, falling back to environment defaults")
        config = _build_env_config()
    _config_store["config"] = config
    _config_store["revision"] += 1
    _registered_revision = -1
    return config


def get_registry() -> AIProviderRegistry:
    return _get_registry()


def get_ai_config() -> AIConfig:
    config = _config_store["config"]
    if config is None:
        config = _build_env_config()
        _config_store["config"] = config
    return config


def ensure_providers_registered() -> None:
    global _registered_revision
    from app.ai.factory import AIProviderFactory

    registry = _get_registry()
    config = get_ai_config()
    revision = _config_store["revision"]
    if registry.count() == 0 or revision != _registered_revision:
        if _registered_revision >= 0:
            registry.clear()
        factory = AIProviderFactory(registry, config)
        factory.register_all()
        _registered_revision = revision


@lru_cache
def _get_prompt_registry() -> PromptTemplateRegistry:
    registry = PromptTemplateRegistry()
    _register_default_prompts(registry)
    return registry


def _register_default_prompts(registry: PromptTemplateRegistry) -> None:
    from app.ai.prompts.template import PromptTemplate

    prompts = [
        # ── Matching AI Prompt ──
        PromptTemplate(
            name="matching-analysis-ai",
            template="""Analyze the job fit between the following candidate profile and job posting.

Job Title: {job_title}
Company: {company}
Job Description: {job_description}

Candidate Profile:
Skills: {profile_skills}
Experience: {profile_experience}
Education: {profile_education}
Current Match Score: {current_score}

Provide a detailed analysis:
1. Why this candidate matches the role
2. Missing skills or qualifications
3. Key strengths
4. Potential weaknesses
5. Specific improvement suggestions
6. Application strategy recommendations

Return as JSON:
{{
  "why_match": string,
  "missing_skills": string[],
  "strengths": string[],
  "weaknesses": string[],
  "improvement_suggestions": string[],
  "application_strategy": string[],
  "enhanced_score": number,
  "confidence": string
}}""",
            system_prompt="You are an expert job matching analyst. Analyze job fit and provide actionable insights.",
            description="AI-powered job matching analysis and enhancement",
        ),
        # ── Project Enhancement AI Prompt ──
        PromptTemplate(
            name="project-enhancement-ai",
            template="""Enhance the following project description to maximize impact.

Project Name: {project_name}
Current Description: {project_description}
Target Role: {target_role}
Target Company: {target_company}
Technologies Used: {technologies}
Job Context: {job_context}

Improve the project description by:
1. Improving wording and professional language
2. Highlighting business impact and value delivered
3. Adding technical depth and complexity details
4. Incorporating ATS-friendly keywords naturally
5. Using strong action verbs and specific metrics
6. Demonstrating problem-solving approach

Do NOT invent achievements, technologies, or outcomes not present in the original.
Maintain complete factual accuracy.

Return as JSON:
{{
  "enhanced_description": string,
  "bullet_points": string[],
  "key_achievements": string[],
  "technologies_highlighted": string[],
  "business_impact": string,
  "changes_summary": string[]
}}""",
            system_prompt="You are a technical writing expert. "
            "Enhance project descriptions while maintaining accuracy.",
            description="AI-powered project description enhancement",
        ),
        # ── Experience Enhancement AI Prompt ──
        PromptTemplate(
            name="experience-enhancement-ai",
            template="""Enhance the following work experience entry for maximum professional impact.

Job Title: {job_title}
Company: {company_name}
Date Range: {date_range}
Current Description: {current_description}
Target Role: {target_role}
Target Company: {target_company}
Job Context: {job_context}

Rewrite the experience bullets to:
1. Use powerful action verbs (led, architect, designed, optimized, etc.)
2. Maintain professional tone and clarity
3. Add specific, quantifiable metrics where supported by facts
4. Optimize for ATS keyword matching
5. Ensure each bullet demonstrates clear value
6. Improve sentence structure and readability

Do NOT invent dates, titles, company names, or achievements.
Preserve all factual information.
Do not fabricate metrics — only include if present in the original.

Return as JSON:
{{
  "improved_bullets": string[],
  "improved_summary": string,
  "key_achievements": string[],
  "metrics_highlighted": string[],
  "skills_demonstrated": string[],
  "changes_summary": string[]
}}""",
            system_prompt="You are a resume optimization expert. "
            "Enhance experience descriptions while maintaining complete factual accuracy.",
            description="AI-powered work experience enhancement",
        ),
        # ── Resume AI Prompts ──
        PromptTemplate(
            name="resume-ai-generation",
            template="""Generate a complete, ATS-optimized resume from the following career profile data.

Career Profile:
{profile_data}

Target Role: {target_role}
Target Company: {target_company}
Section Types: {section_types}

For each section type requested, generate compelling, professional content that:
- Uses strong action verbs
- Quantifies achievements with specific numbers and metrics
- Incorporates relevant industry keywords naturally
- Maintains factual accuracy - never invent experience, titles, or companies
- Uses consistent professional tone throughout
- Optimizes for ATS parsing with standard section headings

Return a JSON object with section_type as key and {{content: string, bullet_points: string[]}} as value.""",
            system_prompt="You are an expert resume writer specializing in ATS-optimized, achievement-focused resumes.",
            description="AI-powered resume generation from career profile data",
        ),
        PromptTemplate(
            name="resume-improvement-ai",
            template="""Improve the following resume section for maximum impact.

Section Type: {section_type}
Current Content:
{current_content}

Target Role: {target_role}
Target Company: {target_company}
Job Description Context: {job_context}

Improvement areas needed: {improvement_areas}

Instructions:
- Use powerful action verbs
- Add specific, quantifiable metrics where possible
- Incorporate relevant keywords from the target role naturally
- Maintain factual accuracy - do not change dates, titles, or company names
- Improve professional tone and clarity
- Keep each bullet concise
- Focus on achievements and business impact

Return the improved content as a JSON object with {{improved_bullets: string[],
summary: string, changes_made: string[]}}.""",
            system_prompt="You are a resume optimization expert. Improve content while maintaining factual accuracy.",
            description="AI-powered resume content improvement",
        ),
        PromptTemplate(
            name="ats-optimization-ai",
            template="""Optimize the following resume for ATS compatibility against a target job.

Resume Content:
{resume_content}

Target Job Title: {job_title}
Target Company: {company}
Job Description: {job_description}

Analyze and optimize across these dimensions:
1. Keyword Match: Identify missing keywords and incorporate them naturally
2. Section Headings: Ensure standard ATS-friendly headings
3. Skills: Optimize skills section for keyword density
4. Bullet Format: Standardize format across all sections

Return as JSON:
{{
  "keyword_analysis": {{"matched": string[], "missing": string[], "recommendations": string[]}},
  "ats_score": number,
  "section_analysis": [{{"section": string, "issues": string[], "suggestions": string[]}}],
  "optimized_content": string,
  "improvement_summary": string[]
}}""",
            system_prompt="You are an ATS optimization specialist. "
            "Optimize resumes for ATS without sacrificing readability.",
            description="AI-powered ATS optimization for resumes",
        ),
        # ── Profile AI Prompts ──
        PromptTemplate(
            name="profile-enhancement-ai",
            template="""Enhance the following professional profile summary and headline.

Current Profile Summary:
{current_profile}

Target Role: {target_role}
Industry: {industry}
Improvement Areas: {improvement_areas}

Enhance while maintaining complete factual accuracy:
1. Professional Summary: Rewrite to be more compelling (2-3 sentences)
2. Headline: Create an attention-grabbing headline
3. Skills: Organize by relevance to target role
4. Achievements: Extract and emphasize key metrics

Note: Experience and project sections are enhanced separately via specialized AI.

Return as JSON:
{{
  "enhanced_summary": string,
  "enhanced_headline": string,
  "skill_recommendations": {{"current": string[], "to_highlight": string[], "to_add": string[]}},
  "achievement_highlights": string[]
}}""",
            system_prompt="You are a professional profile optimization expert. "
            "Enhance profiles for recruiter visibility.",
            description="AI-powered professional profile summary and headline enhancement",
        ),
        PromptTemplate(
            name="skill-recommendations-ai",
            template="""Generate skill development recommendations based on the following profile.

Current Skills: {current_skills}
Target Role: {target_role}
Industry: {industry}
Experience Level: {experience_level}
Job Market Context: {job_market_context}

Provide a skill development plan:
1. Immediate priorities - skills to learn in next 30 days
2. Short-term goals - skills to develop in 1-3 months
3. Long-term growth - skills for 3-6 month development
4. Trending skills in the target role
5. Recommended learning resources

Return as JSON:
{{
  "immediate_priorities": [{{"skill": string, "reason": string, "resources": string[], "estimated_time": string}}],
  "short_term": [{{"skill": string, "reason": string, "resources": string[], "estimated_time": string}}],
  "long_term": [{{"skill": string, "reason": string, "resources": string[], "estimated_time": string}}],
  "trending_skills": string[],
  "role_specific_skills": string[],
  "total_estimated_investment": string
}}""",
            system_prompt="You are a career development advisor. "
            "Provide actionable, market-aware skill recommendations.",
            description="AI-powered skill recommendations and development planning",
        ),
        # ── Interview & Questions AI Prompts ──
        PromptTemplate(
            name="interview-questions-ai",
            template="""Generate comprehensive interview preparation materials.

Job Title: {job_title}
Company: {company}
Job Description: {job_description}
Your Background: {background}
Question Types: {question_types}
Interview Round: {interview_round}

Generate {count} questions each for:
1. Behavioral questions using STAR method
2. Technical questions specific to the role
3. Company culture and fit questions
4. Role-specific scenario questions

For each question provide the question, what the interviewer looks for, key points,
sample structure, and common mistakes.

Return as JSON:
{{
  "behavioral_questions": [{{"question": string, "looking_for": string,
    "key_points": string[], "common_mistakes": string[]}}],
  "technical_questions": [{{"question": string, "looking_for": string,
    "key_points": string[], "common_mistakes": string[]}}],
  "culture_questions": [{{"question": string, "looking_for": string,
    "key_points": string[], "common_mistakes": string[]}}],
  "scenario_questions": [{{"question": string, "looking_for": string,
    "key_points": string[], "common_mistakes": string[]}}],
  "preparation_tips": string[],
  "questions_to_ask": string[]
}}""",
            system_prompt="You are an expert interview preparation coach. "
            "Generate realistic, role-specific interview questions.",
            description="AI-powered interview question generation",
        ),
        PromptTemplate(
            name="application-questions-ai",
            template="""Generate thoughtful answers for job application questions.

Job: {job_title} at {company}
Job Description: {job_description}
Your Profile: {profile_summary}
Questions: {questions}

For each question, provide a tailored answer that:
- References specific experience from the profile
- Aligns with the job requirements
- Demonstrates fit for the role and company
- Is concise but comprehensive

Return as JSON:
{{
  "answers": [{{"question": string, "answer": string, "key_points": string[], "estimated_length": string}}],
  "tips": string[]
}}""",
            system_prompt="You are an expert at answering job application questions. "
            "Provide compelling, tailored responses.",
            description="AI-powered job application question answering",
        ),
        # ── Company Research & Job Summary AI Prompts ──
        PromptTemplate(
            name="company-research-ai",
            template="""Research the following company for interview preparation.

Company Name: {company}
Industry: {industry}
Role: {role}
Company URL: {company_url}

Provide comprehensive company intelligence:
1. Company Overview - business model, size, stage, market position
2. Products & Services - key offerings and differentiators
3. Company Culture - values and work environment
4. Recent News - latest developments
5. Competitors - main competitors
6. Interview Tips - what to emphasize
7. Technology Stack - known technologies used

Return as JSON:
{{
  "company_overview": {{"name": string, "industry": string, "size": string, "business_model": string}},
  "products_services": string[],
  "culture": {{"values": string[], "work_environment": string}},
  "recent_news": [{{"title": string, "summary": string}}],
  "competitors": [{{"name": string}}],
  "interview_tips": string[],
  "tech_stack": string[],
  "talking_points": string[],
  "questions_to_ask": string[]
}}""",
            system_prompt="You are a business research analyst. "
            "Provide actionable company intelligence for interview preparation.",
            description="AI-powered company research and intelligence",
        ),
        PromptTemplate(
            name="job-summary-ai",
            template="""Summarize and analyze the following job posting.

Job Title: {title}
Company: {company}
Description: {description}
Requirements: {requirements}
Preferred Qualifications: {preferred_qualifications}
Your Profile Summary: {profile_summary}

Generate a comprehensive job analysis:
1. Role Summary - concise overview
2. Key Responsibilities - top responsibilities
3. Required Skills - must-have skills
4. Preferred Skills - nice-to-have skills
5. Keywords for ATS
6. Experience Level
7. Fit Score - how well the profile matches (0-100)

Return as JSON:
{{
  "role_summary": string,
  "key_responsibilities": string[],
  "required_skills": [{{"skill": string, "importance": string}}],
  "preferred_skills": string[],
  "ats_keywords": string[],
  "experience_level": string,
  "salary_insight": {{"estimated_range": string, "confidence": string}},
  "fit_score": number,
  "fit_explanation": string,
  "application_strategy": string[]
}}""",
            system_prompt="You are a job market analyst. Provide concise job posting summaries with fit assessment.",
            description="AI-powered job posting summarization and analysis",
        ),
        # ── Email & Communication AI Prompts ──
        PromptTemplate(
            name="email-generation",
            template="""Generate a professional email for a job-related communication.

Email Type: {email_type}
Recipient: {recipient}
Recipient Title: {recipient_title}
Company: {company}
Your Name: {your_name}
Job Title (if applicable): {job_title}
Context/Details: {context}

Supported email types and their purposes:
- recruiter_outreach: Initial message to a recruiter about opportunities
- follow_up: Follow-up after an application or interview
- thank_you: Thank-you email after an interview
- application: Submit application with cover note
- networking: Professional networking message
- referral_request: Request a referral from a connection
- acceptance: Accept a job offer
- negotiation: Negotiate offer terms
- rejection: Politely decline an offer

Generate a professional, well-structured email with appropriate subject line.

Return as JSON:
{{
  "subject": string,
  "body": string,
  "tone": string,
  "key_points": string[]
}}""",
            system_prompt="You are a professional business communication expert. "
            "Generate effective job-related emails.",
            description="AI-powered email generation for job communications",
        ),
        # ── Cover Letter AI Prompts ──
        PromptTemplate(
            name="cover-letter-ai",
            template="""Generate a {style} cover letter for the following position.

Job Title: {job_title}
Company: {company_name}
Job Description: {job_description}
Applicant's Resume: {resume_text}
Tone: {tone}
Hiring Manager: {hiring_manager}

The cover letter should:
- Start with an attention-grabbing opening
- Highlight 2-3 specific achievements matching the job requirements
- Demonstrate knowledge of the company and role
- End with a clear call to action
- Be between 250-400 words
- Use {tone} tone throughout

Return as JSON with {{content: string, subject: string}}.""",
            system_prompt="You are an expert cover letter writer. Write compelling cover letters that get interviews.",
            description="AI-powered cover letter generation",
        ),
        PromptTemplate(
            name="cover-letter-ai-assist",
            template="""Perform the following edit on the given cover letter content.

Instruction: {instruction}
Context: {context}

Content to edit:
{content}

Supported instructions:
- rewrite: Rewrite to be more compelling
- shorten: Shorten while preserving key information
- expand: Expand with more detail
- professional: Make more professional
- technical: Add technical language
- grammar: Fix grammar and spelling
- improve: Improve overall quality
- friendly: Make warmer and approachable
- executive: Focus on leadership and strategy
- remove_repetition: Remove repetitive phrases

Return only the edited text as a JSON object with {{edited_content: string, changes_summary: string}}.""",
            system_prompt="You are a professional editor specializing in cover letter improvement.",
            description="AI-powered cover letter editing assistance",
        ),
        # ── Legacy Compat Prompts (DEPRECATED — kept for backward compat) ──
        # These use different variable names and are superseded by the -ai variants above.
        # New code should use the -ai variants. Remove legacy templates after
        # auditing all callers that reference them by name.
        PromptTemplate(
            name="resume-generation",
            template="""Generate a professional resume section based on the following information.

Job Title: {job_title}
Target Company: {company}
Industry: {industry}
Experience Level: {experience_level}
Key Skills: {skills}
Achievements: {achievements}
Education: {education}

Generate a compelling {section_type} section that highlights relevant experience and achievements.
Tailor the content to the target role and company.
Use strong action verbs and quantify achievements where possible.""",
            system_prompt="You are an expert resume writer. Create ATS-optimized resume content that stands out.",
            description="Generate resume content tailored to a specific job",
        ),
        PromptTemplate(
            name="cover-letter",
            template="""Write a cover letter for the following position.

Job Title: {job_title}
Company: {company_name}
Job Description: {job_description}
Applicant's Resume: {resume_text}
Tone: {tone}
Hiring Manager: {hiring_manager}

Instructions:
- Start with: Dear {salutation},
- Highlight specific skills and experiences that match the job description.
- Reference relevant projects and measurable achievements.
- Explain why the applicant is a good fit for this specific role.
- Keep the letter between 250-400 words.
- End with a professional closing.
{additional_notes}""",
            system_prompt="You are a professional cover letter writer. Write compelling, tailored cover letters.",
            description="Generate a tailored cover letter for a specific job application",
        ),
        PromptTemplate(
            name="resume-improvement",
            template="""Improve the following resume section for a {job_title} position at {company}.

Current content:
{current_content}

Job description context:
{job_context}

Instructions:
- Use stronger action verbs
- Quantify achievements with numbers where possible
- Add relevant keywords from the job description
- Keep the same factual information but present it more impactfully
- Maintain professional tone
- Maximum {max_words} words""",
            system_prompt="You are an expert resume optimization specialist.",
            description="Improve existing resume content for better impact",
        ),
        PromptTemplate(
            name="interview-questions",
            template="""Generate interview preparation questions for the following role.

Job Title: {job_title}
Company: {company}
Job Description: {job_description}
Your Background: {background}
Question Types: {question_types}

Generate:
1. {count} behavioral questions based on the job requirements
2. {count} technical questions relevant to the role
3. {count} company-specific questions about {company}

For each question, provide: the question, what the interviewer is looking for, a suggested
framework for answering, key points to include.""",
            system_prompt="You are an interview preparation coach. "
            "Generate realistic interview questions and guidance.",
            description="Generate interview preparation questions and guidance",
        ),
        PromptTemplate(
            name="company-research",
            template="""Research the following company for a job interview preparation.

Company Name: {company}
Industry: {industry}
Role: {role}

Provide:
1. Company overview and business model
2. Key products/services
3. Recent news and developments
4. Company culture and values
5. Competitors and market position
6. Potential talking points for the interview
7. Questions to ask the interviewer""",
            system_prompt="You are a business research analyst. Provide comprehensive company intelligence.",
            description="Research a company for interview preparation",
        ),
        PromptTemplate(
            name="job-summary",
            template="""Summarize the following job posting.

Job Title: {title}
Company: {company}
Description: {description}
Requirements: {requirements}

Provide:
1. Brief role summary (2-3 sentences)
2. Top 5 required skills
3. Key responsibilities
4. Company overview
5. Fit assessment based on {profile_summary}
6. Salary range insight
7. Growth potential assessment""",
            system_prompt="You are a job market analyst. Provide concise, actionable job posting summaries.",
            description="Summarize a job posting with key insights",
        ),
        PromptTemplate(
            name="profile-enhancement",
            template="""Enhance the following professional profile for better impact.

Current Profile:
{current_profile}

Target Role: {target_role}
Industry: {industry}

Improve:
1. Professional summary/headline
2. Key skills presentation
3. Experience descriptions
4. Achievement highlights

Make the profile more compelling while keeping all factual information accurate.""",
            system_prompt="You are a professional profile optimization expert. "
            "Enhance profiles for maximum career impact.",
            description="Enhance a professional profile for better visibility",
        ),
        PromptTemplate(
            name="skill-suggestions",
            template="""Suggest skill development based on the following profile and target role.

Current Skills: {current_skills}
Target Role: {target_role}
Industry: {industry}
Experience Level: {experience_level}
Job Description: {job_description}

Provide:
1. Skills to acquire (prioritized)
2. Skills to improve/update
3. Emerging skills in the field
4. Recommended learning resources
5. Estimated time to acquire each skill""",
            system_prompt="You are a career development advisor. Provide actionable skill development recommendations.",
            description="Suggest skills to develop for career growth",
        ),
        PromptTemplate(
            name="application-questions",
            template="""Generate answers for the following job application questions.

Job: {job_title} at {company}
Job Description: {job_description}
Your Profile: {profile_summary}
Questions: {questions}

For each question, provide a thoughtful, tailored answer that references specific experience,
aligns with job requirements, and demonstrates fit.""",
            system_prompt="You are an expert at answering job application questions.",
            description="Generate answers to job application questions",
        ),
        PromptTemplate(
            name="ats-optimization",
            template="""Optimize the following resume content for ATS compatibility.

Target Role: {target_role}
Target Company: {target_company}
Job Description Keywords: {keywords}
Current Content: {current_content}

Instructions:
- Incorporate target keywords naturally
- Maintain readability for human reviewers
- Use standard section headings
- Avoid tables, columns, and graphics
- Keep critical information in plain text
- Maximum {max_length} characters""",
            system_prompt="You are an ATS optimization expert. Optimize resumes for applicant tracking systems.",
            description="Optimize resume content for ATS compatibility",
        ),
    ]

    for prompt in prompts:
        registry.register(prompt)

    logger.info("Registered default prompt templates", count=registry.count())


def get_prompt_registry() -> PromptTemplateRegistry:
    return _get_prompt_registry()


def get_ai_service() -> AIService:
    registry = _get_registry()
    config = get_ai_config()
    prompt_registry = _get_prompt_registry()
    ensure_providers_registered()
    return AIService(registry=registry, config=config, prompt_registry=prompt_registry)
