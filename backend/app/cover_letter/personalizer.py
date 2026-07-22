from __future__ import annotations

from app.cover_letter.schemas import PersonalizationData


class Personalizer:
    def extract(self, profile, job_posting, match_result, optimized_resume) -> PersonalizationData:
        company_name = self._get_company_name(job_posting)
        job_title = self._get_job_title(job_posting)

        current_role = None
        years_experience = None
        career_level = None
        primary_skills = []
        strengths = []
        personal_summary = None
        career_goals = None

        if profile:
            current_role = getattr(profile, "current_role", None)
            years_experience = getattr(profile, "years_of_experience", None)
            career_level = getattr(profile, "career_level", None)
            if career_level:
                career_level = str(career_level)
            primary_skills = list(getattr(profile, "primary_skills", []) or [])
            strengths = list(getattr(profile, "strengths", []) or [])
            personal_summary = getattr(profile, "personal_summary", None)
            career_goals = getattr(profile, "career_goals", None)

        matching_skills = []
        if match_result:
            for ms in getattr(match_result, "matching_skills", []) or []:
                name = getattr(ms, "name", "") or ""
                if name:
                    matching_skills.append(name)

        projects = []
        if optimized_resume:
            for sec in getattr(optimized_resume, "project_sections", []) or []:
                title = getattr(sec, "title", None)
                if title:
                    projects.append(title)

        education_summary = None
        if profile:
            education_summary = getattr(profile, "education_summary", None)

        certifications = []
        if profile:
            certifications = list(getattr(profile, "certifications", []) or [])

        industries = []
        if profile:
            industries = list(getattr(profile, "industries", []) or [])

        return PersonalizationData(
            company_name=company_name,
            job_title=job_title,
            current_role=current_role or job_title,
            years_experience=years_experience,
            career_level=career_level or "experienced",
            primary_skills=primary_skills[:8],
            matching_skills=matching_skills,
            strengths=strengths[:3],
            projects=projects[:3],
            education_summary=education_summary,
            certifications=certifications[:5],
            industries=industries[:3],
            career_goals=career_goals,
            personal_summary=personal_summary,
        )

    @staticmethod
    def _get_company_name(job_posting) -> str | None:
        if not job_posting:
            return None
        company = getattr(job_posting, "company", None)
        if company:
            return getattr(company, "name", None)
        return None

    @staticmethod
    def _get_job_title(job_posting) -> str | None:
        if not job_posting:
            return None
        return getattr(job_posting, "title", None)

    def build_variables(
        self,
        data: PersonalizationData,
        tone: str,
        template_style: str,
    ) -> dict[str, str]:
        from app.cover_letter.templates import TONE_SUFFIXES

        tone_suffix = TONE_SUFFIXES.get(tone, "")

        top_strength = data.strengths[0] if data.strengths else "delivering high-quality work"
        primary_skills_list = ", ".join(data.primary_skills[:5]) if data.primary_skills else "relevant technical skills"
        matching_skills_list = ", ".join(data.matching_skills[:5]) if data.matching_skills else primary_skills_list
        matching_skills_count = str(len(data.matching_skills)) if data.matching_skills else "several"
        project_list = ", ".join(data.projects[:3]) if data.projects else "various software development projects"
        years = str(int(data.years_experience)) if data.years_experience else "several"
        industry = data.industries[0] if data.industries else "software"
        technical_skills = ", ".join(data.primary_skills[:3]) if data.primary_skills else "software development"

        company_value = "building innovative solutions"
        industry_focus = "web"

        return {
            "job_title": data.job_title or "the position",
            "company_name": data.company_name or "your company",
            "career_level": data.career_level or "experienced",
            "years_experience": years,
            "current_role": data.current_role or data.job_title or "professional",
            "industry_focus": industry_focus,
            "company_value": company_value,
            "industry": industry,
            "technical_skills": technical_skills,
            "primary_skills_list": primary_skills_list,
            "matching_skills_count": matching_skills_count,
            "matching_skills_list": matching_skills_list,
            "top_strength": top_strength,
            "project_list": project_list,
            "user_name": "Your Name",
            "tone_suffix": tone_suffix,
        }
