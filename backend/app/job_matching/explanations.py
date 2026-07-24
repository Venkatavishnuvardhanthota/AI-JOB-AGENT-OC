from __future__ import annotations

from app.job_matching.schemas import MatchResult


class ExplanationGenerator:
    def generate_summary(self, result: MatchResult) -> str:
        parts: list[str] = []
        parts.append(f"Overall match: {result.overall_match_score:.0f}/100")
        parts.append(f"({result.recommendation.value.replace('_', ' ').title()})")

        matched = len(result.matching_skills)
        missing = len(result.missing_skills)
        parts.append(f"Skills: {matched} matched, {missing} missing")

        if result.skills_score.score >= 70:
            parts.append("Strong skill alignment")
        elif result.skills_score.score >= 40:
            parts.append("Moderate skill alignment")
        else:
            parts.append("Weak skill alignment")

        if result.experience_score.score >= 70:
            parts.append("Experience matches well")
        elif result.experience_score.score >= 40:
            parts.append("Experience partially matches")

        if result.location_score.score >= 70:
            parts.append("Location is compatible")
        elif result.location_score.score < 40:
            parts.append("Location may be a concern")

        if result.salary_score.score >= 70:
            parts.append("Salary expectations align")
        elif result.salary_score.score < 40:
            parts.append("Salary gap exists")

        return " | ".join(parts)

    def generate_improvement_recommendations(self, result: MatchResult) -> list[str]:
        recommendations: list[str] = []

        missing_skills = result.missing_skills
        if missing_skills:
            names = [s.name for s in missing_skills[:5]]
            impact = round((len(missing_skills) / max(len(result.matching_skills) + len(missing_skills), 1)) * 100)
            recommendations.append(f"Learn {', '.join(names)} to increase match by approximately {impact}%")

        if result.skills_score.score < 50:
            recommendations.append("Add more relevant skills to your profile to improve matching")

        if result.salary_score.score < 40 and result.salary_score.score > 0:
            recommendations.append("Consider adjusting salary expectations or targeting roles in a different range")

        if result.location_score.score < 40:
            recommendations.append("Consider remote roles or expanding your location preferences")

        if result.remote_score.score < 40 and result.remote_score.score > 0:
            recommendations.append("Update your remote work preference to match more opportunities")

        if result.education_score.score < 40:
            recommendations.append("Highlight relevant education or certifications")

        if result.experience_score.score < 40:
            recommendations.append("Gain more experience in targeted areas or adjust your career level expectations")

        if result.employment_type_score.score < 40:
            recommendations.append("Consider different employment types for more opportunities")

        if result.industry_score.score < 40:
            recommendations.append("Explore adjacent industries where your skills are transferable")

        return recommendations

    def format_skill_details(self, result: MatchResult) -> list[str]:
        lines: list[str] = []
        lines.append("Matched:")
        for s in result.matching_skills[:10]:
            lines.append(f"  ✓ {s.name}")

        if result.missing_skills:
            lines.append("Missing:")
            for s in result.missing_skills[:10]:
                lines.append(f"  ✗ {s.name}")

        if result.preferred_skills:
            lines.append("Additional skills you have:")
            for s in result.preferred_skills[:5]:
                lines.append(f"  + {s.name}")

        return lines
