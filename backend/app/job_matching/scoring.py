from __future__ import annotations

from app.job_matching.config import MatchingConfig
from app.job_matching.schemas import DimensionScore, MatchRecommendation


class ScoringEngine:
    def __init__(self, config: MatchingConfig) -> None:
        self._config = config

    def compute_overall(
        self,
        skills_score: float,
        experience_score: float,
        education_score: float,
        location_score: float,
        remote_score: float,
        salary_score: float,
        employment_type_score: float,
        career_level_score: float,
        industry_score: float,
        certifications_score: float,
        projects_score: float,
    ) -> float:
        weights = {
            "skills": self._config.skills_weight,
            "experience": self._config.experience_weight,
            "education": self._config.education_weight,
            "location": self._config.location_weight,
            "remote": self._config.remote_weight,
            "salary": self._config.salary_weight,
            "employment_type": self._config.employment_type_weight,
            "career_level": self._config.career_level_weight,
            "industry": self._config.industry_weight,
            "certifications": self._config.certifications_weight,
            "projects": self._config.projects_weight,
        }
        scores = {
            "skills": skills_score,
            "experience": experience_score,
            "education": education_score,
            "location": location_score,
            "remote": remote_score,
            "salary": salary_score,
            "employment_type": employment_type_score,
            "career_level": career_level_score,
            "industry": industry_score,
            "certifications": certifications_score,
            "projects": projects_score,
        }
        total = 0.0
        for key, score in scores.items():
            weight = weights[key]
            total += score * weight
        return round(total, 1)

    def compute_dimension_scores(
        self,
        skills_score: float,
        experience_score: float,
        education_score: float,
        location_score: float,
        remote_score: float,
        salary_score: float,
        employment_type_score: float,
        career_level_score: float,
        industry_score: float,
        certifications_score: float,
        projects_score: float,
    ) -> dict[str, DimensionScore]:
        weights = {
            "skills": self._config.skills_weight,
            "experience": self._config.experience_weight,
            "education": self._config.education_weight,
            "location": self._config.location_weight,
            "remote": self._config.remote_weight,
            "salary": self._config.salary_weight,
            "employment_type": self._config.employment_type_weight,
            "career_level": self._config.career_level_weight,
            "industry": self._config.industry_weight,
            "certifications": self._config.certifications_weight,
            "projects": self._config.projects_weight,
        }
        raw = {
            "skills": skills_score,
            "experience": experience_score,
            "education": education_score,
            "location": location_score,
            "remote": remote_score,
            "salary": salary_score,
            "employment_type": employment_type_score,
            "career_level": career_level_score,
            "industry": industry_score,
            "certifications": certifications_score,
            "projects": projects_score,
        }
        result: dict[str, DimensionScore] = {}
        for key, raw_score in raw.items():
            weight = weights[key]
            result[key] = DimensionScore(
                score=raw_score,
                weight=weight,
                weighted_score=round(raw_score * weight, 1),
            )
        return result

    def compute_confidence(self, overall_score: float, completeness_score: int | None) -> float:
        score_conf = min(1.0, overall_score / 100.0)
        comp_conf = completeness_score / 100.0 if completeness_score is not None else 0.5
        return round((score_conf * 0.6 + comp_conf * 0.4), 2)

    def compute_recommendation(self, overall_score: float) -> MatchRecommendation:
        if overall_score >= self._config.strong_apply_threshold:
            return MatchRecommendation.STRONG_APPLY
        if overall_score >= self._config.apply_threshold:
            return MatchRecommendation.APPLY
        if overall_score >= self._config.consider_threshold:
            return MatchRecommendation.CONSIDER
        if overall_score >= self._config.min_recommendation_threshold:
            return MatchRecommendation.WEAK
        return MatchRecommendation.NOT_RECOMMENDED
