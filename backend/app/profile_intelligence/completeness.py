from __future__ import annotations

from app.profile_intelligence.schemas import ProfileCompleteness


class ProfileCompletenessScorer:
    CATEGORIES: dict[str, float] = {
        "career_profile": 0.15,
        "education": 0.12,
        "experience": 0.18,
        "projects": 0.10,
        "skills": 0.18,
        "certifications": 0.08,
        "languages": 0.05,
        "social_links": 0.05,
        "preferences": 0.09,
    }

    def compute(self, raw: dict) -> ProfileCompleteness:
        scores: dict[str, int] = {}
        missing: list[str] = []

        scores["career_profile"] = self._score_career_profile(raw)
        scores["education"] = self._score_education(raw)
        scores["experience"] = self._score_experience(raw)
        scores["projects"] = self._score_projects(raw)
        scores["skills"] = self._score_skills(raw)
        scores["certifications"] = self._score_certifications(raw)
        scores["languages"] = self._score_languages(raw)
        scores["social_links"] = self._score_social_links(raw)
        scores["preferences"] = self._score_preferences(raw)

        for cat, score in scores.items():
            if score < 50:
                missing.append(cat)

        overall = sum(scores[cat] * weight for cat, weight in self.CATEGORIES.items())

        return ProfileCompleteness(
            overall_score=round(overall),
            categories=scores,
            missing_items=missing,
        )

    def _score_career_profile(self, raw: dict) -> int:
        score = 0
        profile = raw.get("profile")
        if not profile:
            return 0
        if getattr(profile, "headline", None):
            score += 15
        if getattr(profile, "professional_summary", None):
            score += 20
        if getattr(profile, "current_role", None):
            score += 15
        if getattr(profile, "total_years_experience", None) is not None:
            score += 15
        if getattr(profile, "desired_role", None):
            score += 10
        if getattr(profile, "employment_status", None):
            score += 10
        if getattr(profile, "notice_period", None):
            score += 10
        if getattr(profile, "portfolio_url", None):
            score += 5
        return min(score, 100)

    def _score_education(self, raw: dict) -> int:
        education = raw.get("education", [])
        if not education:
            return 0
        score = min(len(education) * 30, 60)
        has_degree = any(getattr(e, "degree", None) for e in education)
        if has_degree:
            score += 20
        has_field = any(getattr(e, "field_of_study", None) for e in education)
        if has_field:
            score += 20
        return min(score, 100)

    def _score_experience(self, raw: dict) -> int:
        experiences = raw.get("experience", [])
        if not experiences:
            return 0
        score = min(len(experiences) * 20, 60)
        has_responsibilities = any(getattr(e, "responsibilities", None) for e in experiences)
        if has_responsibilities:
            score += 20
        has_achievements = any(getattr(e, "achievements", None) for e in experiences)
        if has_achievements:
            score += 20
        return min(score, 100)

    def _score_projects(self, raw: dict) -> int:
        projects = raw.get("projects", [])
        if not projects:
            return 0
        score = min(len(projects) * 30, 60)
        has_tech = any(getattr(p, "technologies", None) for p in projects)
        if has_tech:
            score += 20
        has_url = any(getattr(p, "github_url", None) or getattr(p, "demo_url", None) for p in projects)
        if has_url:
            score += 20
        return min(score, 100)

    def _score_skills(self, raw: dict) -> int:
        skills = raw.get("skills", [])
        if not skills:
            return 0
        score = min(len(skills) * 8, 60)
        has_proficiency = any(getattr(s, "proficiency", None) for s in skills)
        if has_proficiency:
            score += 20
        has_category = any(getattr(s, "category", None) for s in skills)
        if has_category:
            score += 20
        return min(score, 100)

    def _score_certifications(self, raw: dict) -> int:
        certs = raw.get("certifications", [])
        if not certs:
            return 0
        score = min(len(certs) * 25, 60)
        has_issuer = any(getattr(c, "issuer", None) for c in certs)
        if has_issuer:
            score += 20
        has_url = any(getattr(c, "credential_url", None) for c in certs)
        if has_url:
            score += 20
        return min(score, 100)

    def _score_languages(self, raw: dict) -> int:
        languages = raw.get("languages", [])
        if not languages:
            return 0
        score = min(len(languages) * 25, 50)
        has_proficiency = any(getattr(lang, "proficiency", None) for lang in languages)
        if has_proficiency:
            score += 50
        return min(score, 100)

    def _score_social_links(self, raw: dict) -> int:
        profile = raw.get("profile")
        score = 0
        if profile:
            if getattr(profile, "linkedin_url", None):
                score += 30
            if getattr(profile, "github_url", None):
                score += 25
            if getattr(profile, "portfolio_url", None):
                score += 25
            if getattr(profile, "website_url", None):
                score += 20
        social_links = raw.get("social_links", [])
        if social_links:
            score += min(len(social_links) * 10, 30)
        return min(score, 100)

    def _score_preferences(self, raw: dict) -> int:
        preferences = raw.get("preferences")
        if not preferences:
            score = 0
            if raw.get("profile") and getattr(raw["profile"], "expected_salary", None) is not None:
                score += 30
            if raw.get("profile") and getattr(raw["profile"], "willing_to_relocate", None) is not None:
                score += 20
            return min(score, 100)
        score = 0
        if getattr(preferences, "preferred_titles", None):
            score += 20
        if getattr(preferences, "preferred_locations", None):
            score += 20
        if getattr(preferences, "employment_types", None):
            score += 20
        if getattr(preferences, "work_modes", None):
            score += 20
        if getattr(preferences, "minimum_salary", None) is not None:
            score += 20
        return min(score, 100)
