from __future__ import annotations

from typing import Any

import structlog

from app.ai.dependencies import get_ai_service

logger = structlog.get_logger(__name__)


async def ai_generate_resume(
    profile_data: str,
    target_role: str = "",
    target_company: str = "",
    section_types: list[str] | None = None,
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="resume-ai-generation",
        variables={
            "profile_data": profile_data,
            "target_role": target_role,
            "target_company": target_company,
            "section_types": ", ".join(section_types) if section_types else "summary, experience, education, skills, projects",
        },
        max_tokens=3000,
    )
    return {"sections": result.content, "provider": result.provider, "model": result.model}


async def ai_improve_resume_section(
    section_type: str,
    current_content: str,
    target_role: str = "",
    target_company: str = "",
    job_context: str = "",
    improvement_areas: str = "grammar, tone, action_verbs, keywords",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="resume-improvement-ai",
        variables={
            "section_type": section_type,
            "current_content": current_content,
            "target_role": target_role,
            "target_company": target_company,
            "job_context": job_context,
            "improvement_areas": improvement_areas,
        },
        max_tokens=2000,
    )
    return {"improved_content": result.content, "provider": result.provider, "model": result.model}


async def ai_optimize_ats(
    resume_content: str,
    job_title: str = "",
    company: str = "",
    job_description: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="ats-optimization-ai",
        variables={
            "resume_content": resume_content,
            "job_title": job_title,
            "company": company,
            "job_description": job_description,
        },
        max_tokens=3000,
    )
    return {"optimization": result.content, "provider": result.provider, "model": result.model}


async def ai_enhance_profile(
    current_profile: str,
    target_role: str = "",
    industry: str = "",
    improvement_areas: str = "summary, headline, skills, achievements",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="profile-enhancement-ai",
        variables={
            "current_profile": current_profile,
            "target_role": target_role,
            "industry": industry,
            "improvement_areas": improvement_areas,
        },
        max_tokens=2000,
    )
    return {"enhanced_profile": result.content, "provider": result.provider, "model": result.model}


async def ai_enhance_profile_delegated(
    current_profile: str,
    target_role: str = "",
    industry: str = "",
    target_company: str = "",
    experience_entries: list[dict] | None = None,
    project_entries: list[dict] | None = None,
    improvement_areas: str = "summary, headline, skills, achievements",
) -> dict[str, Any]:
    profile_result = await ai_enhance_profile(
        current_profile=current_profile,
        target_role=target_role,
        industry=industry,
        improvement_areas=improvement_areas,
    )

    enhanced_experience = []
    if experience_entries:
        for entry in experience_entries:
            exp_result = await ai_enhance_experience(
                job_title=entry.get("title", ""),
                company_name=entry.get("company", ""),
                current_description=entry.get("description", ""),
                target_role=target_role,
                target_company=target_company,
                date_range=entry.get("date_range", ""),
                job_context=entry.get("job_context", ""),
            )
            enhanced_experience.append(exp_result.get("improved_experience", ""))

    enhanced_projects = []
    if project_entries:
        for entry in project_entries:
            proj_result = await ai_enhance_project(
                project_name=entry.get("name", ""),
                project_description=entry.get("description", ""),
                target_role=target_role,
                target_company=target_company,
                technologies=entry.get("technologies", ""),
                job_context=entry.get("job_context", ""),
            )
            enhanced_projects.append(proj_result.get("enhanced_description", ""))

    return {
        **profile_result,
        "enhanced_experience": enhanced_experience or None,
        "enhanced_projects": enhanced_projects or None,
    }


async def ai_enhance_project(
    project_name: str,
    project_description: str,
    target_role: str = "",
    target_company: str = "",
    technologies: str = "",
    job_context: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="project-enhancement-ai",
        variables={
            "project_name": project_name,
            "project_description": project_description,
            "target_role": target_role,
            "target_company": target_company,
            "technologies": technologies,
            "job_context": job_context,
        },
        max_tokens=2000,
    )
    return {
        "enhanced_description": result.content,
        "provider": result.provider,
        "model": result.model,
    }


async def ai_enhance_experience(
    job_title: str,
    company_name: str,
    current_description: str,
    target_role: str = "",
    target_company: str = "",
    date_range: str = "",
    job_context: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="experience-enhancement-ai",
        variables={
            "job_title": job_title,
            "company_name": company_name,
            "current_description": current_description,
            "target_role": target_role,
            "target_company": target_company,
            "date_range": date_range,
            "job_context": job_context,
        },
        max_tokens=2000,
    )
    return {
        "improved_experience": result.content,
        "provider": result.provider,
        "model": result.model,
    }


async def ai_recommend_skills(
    current_skills: str,
    target_role: str = "",
    industry: str = "",
    experience_level: str = "",
    job_market_context: str = "",
) -> dict[str, Any]:
    ai_service = get_ai_service()
    result = await ai_service.generate_prompted(
        template_name="skill-recommendations-ai",
        variables={
            "current_skills": current_skills,
            "target_role": target_role,
            "industry": industry,
            "experience_level": experience_level,
            "job_market_context": job_market_context,
        },
        max_tokens=2500,
    )
    return {"recommendations": result.content, "provider": result.provider, "model": result.model}
