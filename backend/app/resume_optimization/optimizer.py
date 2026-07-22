from __future__ import annotations

from app.resume_optimization.ats import ATSScorer
from app.resume_optimization.config import OptimizationConfig
from app.resume_optimization.keyword_extractor import KeywordExtractor
from app.resume_optimization.schemas import (
    ATSAssessment,
    ChangeLogEntry,
    ChangeType,
    KeywordAnalysis,
    OptimizationSummary,
    OptimizedResume,
    OptimizedSection,
)
from app.resume_optimization.section_optimizer import SectionOptimizer


class ResumeOptimizer:
    def __init__(
        self,
        config: OptimizationConfig,
        keyword_extractor: KeywordExtractor,
        section_optimizer: SectionOptimizer,
        ats_scorer: ATSScorer,
    ) -> None:
        self._config = config
        self._keyword_extractor = keyword_extractor
        self._section_optimizer = section_optimizer
        self._ats_scorer = ats_scorer

    def optimize(
        self,
        resume,
        job_posting,
        profile,
        match_result,
    ) -> OptimizedResume:
        keywords = self._keyword_extractor.extract(job_posting, match_result)
        resume_sections = self._parse_resume_sections(resume)
        profile_summary = getattr(profile, "personal_summary", None) if profile else None

        change_log: list[ChangeLogEntry] = []
        sections_optimized = 0
        keywords_added = 0
        bullets_rewritten = 0
        items_reordered = 0

        original_summary = resume_sections.get("summary")
        optimized_summary, summary_log = self._section_optimizer.optimize_summary(
            original_summary, profile_summary, keywords,
        )
        if summary_log:
            change_log.append(summary_log)
            if summary_log.change_type != ChangeType.UNCHANGED:
                sections_optimized += 1

        original_skills = resume_sections.get("skills_list", [])
        optimized_skills, skills_log = self._section_optimizer.optimize_skills(
            original_skills, keywords,
        )
        if skills_log:
            change_log.append(skills_log)
            if skills_log.change_type != ChangeType.UNCHANGED:
                items_reordered += 1

        experience_sections, exp_logs = self._optimize_experience_sections(
            resume_sections.get("experience", []), keywords,
        )
        for log in exp_logs:
            change_log.append(log)
            if "Enhanced" in (log.description or ""):
                bullets_rewritten += 1

        project_sections, proj_logs = self._section_optimizer.optimize_projects(
            resume_sections.get("projects", []), keywords,
        )
        for log in proj_logs:
            change_log.append(log)
            items_reordered += 1

        education_sections, edu_logs = self._section_optimizer.optimize_education(
            resume_sections.get("education", []), keywords,
        )
        for log in edu_logs:
            change_log.append(log)
            items_reordered += 1

        cert_sections, cert_logs = self._section_optimizer.optimize_certifications(
            resume_sections.get("certifications", []), keywords,
        )
        for log in cert_logs:
            change_log.append(log)

        other_sections = resume_sections.get("other", [])

        ats_before = self._compute_ats_before(resume_sections, keywords)
        ats_after = self._compute_ats_after(
            keywords, optimized_summary, optimized_skills,
            experience_sections,
        )

        summary = OptimizationSummary(
            original_ats_score=ats_before.overall_score,
            optimized_ats_score=ats_after.overall_score,
            sections_optimized=sections_optimized,
            keywords_added=keywords_added,
            bullets_rewritten=bullets_rewritten,
            items_reordered=items_reordered,
        )

        return OptimizedResume(
            profile_hash=getattr(profile, "profile_hash", None) if profile else None,
            job_hash=self._compute_job_hash(job_posting),
            professional_summary=optimized_summary,
            skills=optimized_skills,
            experience_sections=experience_sections,
            project_sections=project_sections,
            education_sections=education_sections,
            certification_sections=cert_sections,
            other_sections=other_sections,
            keyword_analysis=keywords,
            ats_assessment=ats_after,
            optimization_summary=summary,
            change_log=change_log,
        )

    def _optimize_experience_sections(
        self,
        sections: list[OptimizedSection],
        keywords: KeywordAnalysis,
    ) -> tuple[list[OptimizedSection], list[ChangeLogEntry]]:
        logs: list[ChangeLogEntry] = []
        optimized: list[OptimizedSection] = []
        for sec in sections:
            opt_sec, log = self._section_optimizer.optimize_experience_bullets(sec, keywords)
            optimized.append(opt_sec)
            if log:
                logs.append(log)
        return optimized, logs

    def _parse_resume_sections(self, resume) -> dict:
        result: dict = {
            "summary": None,
            "skills_list": [],
            "experience": [],
            "projects": [],
            "education": [],
            "certifications": [],
            "other": [],
        }

        if not resume:
            return result

        sections = getattr(resume, "sections", None) or []
        content = getattr(resume, "content", None) or {}

        for section in sections:
            section_type = getattr(section, "section_type", "custom") or "custom"
            title = getattr(section, "title", None)
            section_content = getattr(section, "content", None) or {}

            sec = OptimizedSection(
                section_type=section_type,
                title=title,
                original_content=self._serialize_content(section_content),
            )

            if section_type in ("summary", "professional_summary"):
                result["summary"] = self._serialize_content(section_content)
            elif section_type == "skills":
                skills = section_content.get("skills", []) if isinstance(section_content, dict) else []
                result["skills_list"] = list(skills) if skills else []
            elif section_type == "experience":
                result["experience"].append(sec)
            elif section_type in ("project", "projects"):
                result["projects"].append(sec)
            elif section_type in ("education",):
                result["education"].append(sec)
            elif section_type in ("certification", "certifications"):
                result["certifications"].append(sec)
            else:
                result["other"].append(sec)

        if isinstance(content, dict):
            if not result["summary"] and content.get("summary"):
                result["summary"] = str(content["summary"])
            if not result["skills_list"] and content.get("skills"):
                result["skills_list"] = list(content["skills"]) if isinstance(content["skills"], list) else []

        return result

    @staticmethod
    def _serialize_content(content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            parts: list[str] = []
            for _key, value in content.items():
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, list):
                    parts.extend(str(v) for v in value)
            return "\n".join(parts)
        return str(content) if content else ""

    def _compute_ats_before(self, resume_sections: dict, keywords: KeywordAnalysis) -> ATSAssessment:
        summary = resume_sections.get("summary")
        skills = resume_sections.get("skills_list", [])
        experience_text = "\n".join(
            str(getattr(s, "original_content", "")) for s in resume_sections.get("experience", [])
        )
        has_summary = bool(summary)
        has_skills = bool(skills)
        has_experience = bool(resume_sections.get("experience"))
        has_education = bool(resume_sections.get("education"))
        has_projects = bool(resume_sections.get("projects"))
        has_certs = bool(resume_sections.get("certifications"))

        return self._ats_scorer.assess(
            keywords=keywords,
            has_summary=has_summary,
            has_skills_section=has_skills,
            has_experience_section=has_experience,
            has_education_section=has_education,
            has_projects_section=has_projects,
            has_certifications_section=has_certs,
            skill_count=len(skills),
            summary_text=summary,
            experience_text=experience_text,
        )

    def _compute_ats_after(
        self,
        keywords: KeywordAnalysis,
        summary: str | None,
        skills: list[str],
        experience_sections: list[OptimizedSection],
    ) -> ATSAssessment:
        experience_text = "\n".join(
            str(getattr(s, "optimized_content", "")) for s in experience_sections
        )
        return self._ats_scorer.assess(
            keywords=keywords,
            has_summary=bool(summary),
            has_skills_section=bool(skills),
            has_experience_section=bool(experience_sections),
            has_education_section=True,
            has_projects_section=False,
            has_certifications_section=False,
            skill_count=len(skills),
            summary_text=summary,
            experience_text=experience_text,
        )

    @staticmethod
    def _compute_job_hash(job) -> str | None:
        if not job:
            return None
        import hashlib
        import json
        data = {
            "title": getattr(job, "title", None),
            "skills": getattr(job, "skills", None),
        }
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
