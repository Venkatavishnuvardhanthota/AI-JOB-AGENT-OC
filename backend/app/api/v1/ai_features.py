from __future__ import annotations

from fastapi import APIRouter, Depends

from app.ai.dependencies import get_ai_service
from app.ai.exceptions import AIError
from app.core.exceptions import ProviderError
from app.ai.features.schemas import (
    AIFeatureResponse,
    ApplicationQuestionsRequest,
    ATSOptimizeRequest,
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
from app.ai.service import AIService
from app.api.deps import get_current_user

router = APIRouter()


@router.post(
    "/resume/generate",
    summary="AI-powered resume generation",
    response_model=AIFeatureResponse,
)
async def ai_resume_generate(
    body: ResumeGenerateRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.resume import ai_generate_resume

    try:
        result = await ai_generate_resume(
            profile_data=body.profile_data,
            target_role=body.target_role,
            target_company=body.target_company,
            section_types=body.section_types,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/resume/improve",
    summary="AI-powered resume improvement",
    response_model=AIFeatureResponse,
)
async def ai_resume_improve(
    body: ResumeImproveRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.resume import ai_improve_resume_section

    try:
        result = await ai_improve_resume_section(
            section_type=body.section_type,
            current_content=body.current_content,
            target_role=body.target_role,
            target_company=body.target_company,
            job_context=body.job_context,
            improvement_areas=body.improvement_areas,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/resume/ats-optimize",
    summary="AI-powered ATS optimization",
    response_model=AIFeatureResponse,
)
async def ai_resume_ats_optimize(
    body: ATSOptimizeRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.resume import ai_optimize_ats

    try:
        result = await ai_optimize_ats(
            resume_content=body.resume_content,
            job_title=body.job_title,
            company=body.company,
            job_description=body.job_description,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/resume/project-enhance",
    summary="AI-powered project description enhancement",
    response_model=AIFeatureResponse,
)
async def ai_resume_project_enhance(
    body: ProjectEnhanceRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.resume import ai_enhance_project

    try:
        result = await ai_enhance_project(
            project_name=body.project_name,
            project_description=body.project_description,
            target_role=body.target_role,
            target_company=body.target_company,
            technologies=body.technologies,
            job_context=body.job_context,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/resume/experience-enhance",
    summary="AI-powered experience description enhancement",
    response_model=AIFeatureResponse,
)
async def ai_resume_experience_enhance(
    body: ExperienceEnhanceRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.resume import ai_enhance_experience

    try:
        result = await ai_enhance_experience(
            job_title=body.job_title,
            company_name=body.company_name,
            current_description=body.current_description,
            target_role=body.target_role,
            target_company=body.target_company,
            date_range=body.date_range,
            job_context=body.job_context,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/profile/enhance",
    summary="AI-powered profile enhancement",
    response_model=AIFeatureResponse,
)
async def ai_profile_enhance(
    body: ProfileEnhanceRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.resume import ai_enhance_profile_delegated

    try:
        result = await ai_enhance_profile_delegated(
            current_profile=body.current_profile,
            target_role=body.target_role,
            industry=body.industry,
            target_company=body.target_company,
            experience_entries=body.experience_entries,
            project_entries=body.project_entries,
            improvement_areas=body.improvement_areas,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/profile/skills-recommend",
    summary="AI-powered skill recommendations",
    response_model=AIFeatureResponse,
)
async def ai_skills_recommend(
    body: SkillsRecommendRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.resume import ai_recommend_skills

    try:
        result = await ai_recommend_skills(
            current_skills=body.current_skills,
            target_role=body.target_role,
            industry=body.industry,
            experience_level=body.experience_level,
            job_market_context=body.job_market_context,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/interview/questions",
    summary="AI-powered interview question generation",
    response_model=AIFeatureResponse,
)
async def ai_interview_questions(
    body: InterviewQuestionsRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.interview import ai_generate_interview_questions

    try:
        result = await ai_generate_interview_questions(
            job_title=body.job_title,
            company=body.company,
            job_description=body.job_description,
            background=body.background,
            question_types=body.question_types,
            interview_round=body.interview_round.value,
            count=body.count,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/interview/application-questions",
    summary="AI-powered application question answering",
    response_model=AIFeatureResponse,
)
async def ai_application_questions(
    body: ApplicationQuestionsRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.interview import ai_answer_application_questions

    try:
        result = await ai_answer_application_questions(
            job_title=body.job_title,
            company=body.company,
            job_description=body.job_description,
            profile_summary=body.profile_summary,
            questions=body.questions,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/company/research",
    summary="AI-powered company research",
    response_model=AIFeatureResponse,
)
async def ai_company_research(
    body: CompanyResearchRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.company_research import ai_company_research

    try:
        result = await ai_company_research(
            company=body.company,
            industry=body.industry,
            role=body.role,
            company_url=body.company_url,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/job/summarize",
    summary="AI-powered job description summarization",
    response_model=AIFeatureResponse,
)
async def ai_job_summarize(
    body: JobSummaryRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.company_research import ai_job_summary

    try:
        result = await ai_job_summary(
            title=body.title,
            company=body.company,
            description=body.description,
            requirements=body.requirements,
            preferred_qualifications=body.preferred_qualifications,
            profile_summary=body.profile_summary,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/email/generate",
    summary="AI-powered email generation",
    response_model=AIFeatureResponse,
)
async def ai_email_generate(
    body: EmailGenerateRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.email import ai_generate_email

    try:
        result = await ai_generate_email(
            email_type=body.email_type.value,
            recipient=body.recipient,
            recipient_title=body.recipient_title,
            company=body.company,
            your_name=body.your_name,
            job_title=body.job_title,
            context=body.context,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/matching/enhance",
    summary="AI-powered job matching enhancement",
    response_model=AIFeatureResponse,
)
async def ai_matching_enhance(
    body: MatchingEnhanceRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.matching import ai_enhance_matching

    try:
        result = await ai_enhance_matching(
            job_title=body.job_title,
            company=body.company,
            job_description=body.job_description,
            profile_skills=body.profile_skills,
            profile_experience=body.profile_experience,
            profile_education=body.profile_education,
            current_score=body.current_score,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/cover-letter/generate",
    summary="AI-powered cover letter generation",
    response_model=AIFeatureResponse,
)
async def ai_cover_letter_generate(
    body: CoverLetterGenerateRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.cover_letter import ai_generate_cover_letter

    try:
        result = await ai_generate_cover_letter(
            job_title=body.job_title,
            company_name=body.company_name,
            job_description=body.job_description,
            resume_text=body.resume_text,
            tone=body.tone.value,
            style=body.style.value,
            hiring_manager=body.hiring_manager,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})


@router.post(
    "/cover-letter/assist",
    summary="AI-powered cover letter editing assistance",
    response_model=AIFeatureResponse,
)
async def ai_cover_letter_assist(
    body: CoverLetterAssistRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user=Depends(get_current_user),
):
    from app.ai.features.cover_letter import ai_assist_cover_letter

    try:
        result = await ai_assist_cover_letter(
            content=body.content,
            instruction=body.instruction,
            context=body.context,
        )
        return AIFeatureResponse(data=result)
    except AIError as exc:
        raise ProviderError(exc.message, details={"code": exc.code})
