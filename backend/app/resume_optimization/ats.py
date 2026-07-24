from __future__ import annotations

from app.resume_optimization.schemas import ATSAssessment, KeywordAnalysis


class ATSScorer:
    REQUIRED_SECTIONS: set[str] = {
        "professional_summary",
        "skills",
        "experience",
        "education",
    }

    def assess(
        self,
        keywords: KeywordAnalysis,
        has_summary: bool,
        has_skills_section: bool,
        has_experience_section: bool,
        has_education_section: bool,
        has_projects_section: bool,
        has_certifications_section: bool,
        skill_count: int,
        summary_text: str | None,
        experience_text: str | None,
    ) -> ATSAssessment:
        keyword_match = self._score_keyword_match(keywords)
        section_coverage = self._score_section_coverage(
            has_summary,
            has_skills_section,
            has_experience_section,
            has_education_section,
            has_projects_section,
            has_certifications_section,
        )
        keyword_placement = self._score_keyword_placement(
            keywords,
            summary_text,
            experience_text,
        )
        format_compatibility = self._score_format_compatibility(skill_count)

        weights = {
            "keyword_match": 0.35,
            "section_coverage": 0.25,
            "keyword_placement": 0.25,
            "format_compatibility": 0.15,
        }
        overall = round(
            keyword_match * weights["keyword_match"]
            + section_coverage * weights["section_coverage"]
            + keyword_placement * weights["keyword_placement"]
            + format_compatibility * weights["format_compatibility"]
        )

        suggestions = self._generate_suggestions(
            keyword_match,
            section_coverage,
            keyword_placement,
            format_compatibility,
            keywords,
            has_summary,
        )

        return ATSAssessment(
            overall_score=overall,
            keyword_match=keyword_match,
            section_coverage=section_coverage,
            format_compatibility=format_compatibility,
            keyword_placement=keyword_placement,
            suggestions=suggestions,
        )

    @staticmethod
    def _score_keyword_match(keywords: KeywordAnalysis) -> int:
        total = len(keywords.required_keywords) + len(keywords.preferred_keywords) + len(keywords.technical_skills)
        if total == 0:
            return 50
        missing = len(keywords.missing_required)
        matched = total - missing
        return min(100, int((matched / total) * 100))

    @staticmethod
    def _score_section_coverage(
        has_summary: bool,
        has_skills: bool,
        has_experience: bool,
        has_education: bool,
        has_projects: bool,
        has_certs: bool,
    ) -> int:
        score = 0
        if has_summary:
            score += 20
        if has_skills:
            score += 25
        if has_experience:
            score += 25
        if has_education:
            score += 15
        if has_projects:
            score += 10
        if has_certs:
            score += 5
        return min(100, score)

    @staticmethod
    def _score_keyword_placement(
        keywords: KeywordAnalysis,
        summary: str | None,
        experience: str | None,
    ) -> int:
        all_kw = set(
            k.lower()
            for k in (
                keywords.required_keywords + keywords.preferred_keywords + keywords.technical_skills + keywords.tools
            )
        )
        if not all_kw:
            return 50

        placed = 0
        for kw in all_kw:
            in_summary = summary and kw in summary.lower()
            in_experience = experience and kw in experience.lower()
            if in_summary or in_experience:
                placed += 1

        return min(100, int((placed / len(all_kw)) * 100))

    @staticmethod
    def _score_format_compatibility(skill_count: int) -> int:
        score = 70
        if skill_count >= 10:
            score += 15
        elif skill_count >= 5:
            score += 10
        elif skill_count >= 3:
            score += 5
        if skill_count > 30:
            score -= 10
        return min(100, max(0, score))

    @staticmethod
    def _generate_suggestions(
        keyword_match: int,
        section_coverage: int,
        keyword_placement: int,
        format_compatibility: int,
        keywords: KeywordAnalysis,
        has_summary: bool,
    ) -> list[str]:
        suggestions: list[str] = []
        if keyword_match < 70:
            suggestions.append("Add more required keywords from the job description")
        if section_coverage < 70:
            missing = []
            if not has_summary:
                missing.append("professional summary")
            suggestions.append(f"Add missing sections: {', '.join(missing)}")
        if keyword_placement < 70:
            suggestions.append("Include key skills in the professional summary and experience sections")
        if format_compatibility < 70:
            suggestions.append("Reduce skills list to 15-20 most relevant skills")
        if keywords.missing_required:
            names = keywords.missing_required[:3]
            suggestions.append(f"Add missing required skills: {', '.join(names)}")
        return suggestions
