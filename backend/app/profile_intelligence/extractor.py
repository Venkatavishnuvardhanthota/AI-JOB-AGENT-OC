from __future__ import annotations

from datetime import datetime, timezone

import structlog

from app.profile_intelligence.schemas import (
    Availability,
    CareerLevel,
    LanguageInfo,
    TechnicalStack,
)

logger = structlog.get_logger(__name__)

TECH_CLASSIFICATION: dict[str, str] = {
    "python": "programming_languages",
    "javascript": "programming_languages",
    "typescript": "programming_languages",
    "java": "programming_languages",
    "go": "programming_languages",
    "golang": "programming_languages",
    "rust": "programming_languages",
    "c#": "programming_languages",
    "csharp": "programming_languages",
    "c++": "programming_languages",
    "ruby": "programming_languages",
    "php": "programming_languages",
    "swift": "programming_languages",
    "kotlin": "programming_languages",
    "scala": "programming_languages",
    "r": "programming_languages",
    "dart": "programming_languages",
    "sql": "programming_languages",
    "html": "programming_languages",
    "css": "programming_languages",
    "shell": "programming_languages",
    "bash": "programming_languages",
    "powershell": "programming_languages",
    "react": "frameworks",
    "react.js": "frameworks",
    "reactjs": "frameworks",
    "angular": "frameworks",
    "vue": "frameworks",
    "vue.js": "frameworks",
    "django": "frameworks",
    "flask": "frameworks",
    "fastapi": "frameworks",
    "express": "frameworks",
    "express.js": "frameworks",
    "node.js": "frameworks",
    "node": "frameworks",
    "spring": "frameworks",
    "spring boot": "frameworks",
    "asp.net": "frameworks",
    "rails": "frameworks",
    "laravel": "frameworks",
    "tensorflow": "frameworks",
    "pytorch": "frameworks",
    "pandas": "frameworks",
    "numpy": "frameworks",
    "scikit-learn": "frameworks",
    "jquery": "frameworks",
    "bootstrap": "frameworks",
    "tailwind": "frameworks",
    "next.js": "frameworks",
    "nextjs": "frameworks",
    "nuxt": "frameworks",
    ".net": "frameworks",
    "dotnet": "frameworks",
    "postgresql": "databases",
    "postgres": "databases",
    "mysql": "databases",
    "mongodb": "databases",
    "mongo": "databases",
    "redis": "databases",
    "sqlite": "databases",
    "oracle": "databases",
    "mariadb": "databases",
    "cassandra": "databases",
    "dynamodb": "databases",
    "elasticsearch": "databases",
    "firebase": "databases",
    "bigquery": "databases",
    "snowflake": "databases",
    "aws": "cloud_platforms",
    "amazon web services": "cloud_platforms",
    "azure": "cloud_platforms",
    "gcp": "cloud_platforms",
    "google cloud": "cloud_platforms",
    "google cloud platform": "cloud_platforms",
    "docker": "cloud_platforms",
    "kubernetes": "cloud_platforms",
    "k8s": "cloud_platforms",
    "terraform": "cloud_platforms",
    "jenkins": "cloud_platforms",
    "heroku": "cloud_platforms",
    "vercel": "cloud_platforms",
    "netlify": "cloud_platforms",
    "digitalocean": "cloud_platforms",
    "git": "tools",
    "github": "tools",
    "gitlab": "tools",
    "jira": "tools",
    "confluence": "tools",
    "slack": "tools",
    "figma": "tools",
    "adobe": "tools",
    "photoshop": "tools",
    "illustrator": "tools",
    "tableau": "tools",
    "power bi": "tools",
    "powerbi": "tools",
    "looker": "tools",
    "grafana": "tools",
    "prometheus": "tools",
    "datadog": "tools",
    "new relic": "tools",
    "sentry": "tools",
    "kafka": "tools",
    "rabbitmq": "tools",
    "nginx": "tools",
    "apache": "tools",
    "ansible": "tools",
    "puppet": "tools",
    "chef": "tools",
    "circleci": "tools",
    "github actions": "tools",
    "gitlab ci": "tools",
    "agile": "tools",
    "scrum": "tools",
}

SKILL_SYNONYMS: dict[str, str] = {
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "node": "node.js",
    "expressjs": "express",
    "express.js": "express",
    "golang": "go",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "k8s": "kubernetes",
    "gcp": "google cloud platform",
    "amazon web services": "aws",
    "powerbi": "power bi",
    "dotnet": ".net",
    "csharp": "c#",
    "react native": "react",
    "nextjs": "next.js",
    "nuxtjs": "nuxt",
    "typescript": "typescript",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
}


class ProfileExtractor:
    def extract_primary_skills(
        self,
        skill_names: list[str],
        proficiencies: list[str | None],
        years_list: list[float | None],
    ) -> tuple[list[str], list[str]]:
        normalized = [self._normalize_skill(s) for s in skill_names]
        unique = self._deduplicate_skills(normalized)
        scored = [(s, self._skill_priority(s, proficiencies, years_list)) for s in unique]
        scored.sort(key=lambda x: -x[1])
        return [s for s, _ in scored[:5]], [s for s, _ in scored[5:]]

    def classify_technical_stack(self, skills: list[str]) -> TechnicalStack:
        classified: dict[str, list[str]] = {
            "programming_languages": [],
            "frameworks": [],
            "databases": [],
            "cloud_platforms": [],
            "tools": [],
        }
        for skill in skills:
            lower = skill.lower().strip()
            category = TECH_CLASSIFICATION.get(lower)
            if category:
                classified[category].append(skill)
        return TechnicalStack(**classified)

    def infer_career_level(
        self,
        current_role: str | None,
        years_exp: float | None,
    ) -> CareerLevel:
        if years_exp is not None:
            if years_exp < 1:
                return CareerLevel.ENTRY
            if years_exp < 3:
                return CareerLevel.JUNIOR
            if years_exp < 6:
                return CareerLevel.MID
            if years_exp < 10:
                return CareerLevel.SENIOR
            if years_exp < 15:
                return CareerLevel.LEAD
            return CareerLevel.EXECUTIVE

        if current_role:
            lower = current_role.lower()
            if any(kw in lower for kw in ("ceo", "cto", "vp", "vice president", "chief", "director", "head")):
                return CareerLevel.EXECUTIVE
            if any(kw in lower for kw in ("lead", "principal", "staff", "architect")):
                return CareerLevel.LEAD
            if any(kw in lower for kw in ("senior", "sr", "expert")):
                return CareerLevel.SENIOR
            if any(kw in lower for kw in ("junior", "jr", "graduate", "entry")):
                return CareerLevel.JUNIOR
            if any(kw in lower for kw in ("intern", "trainee")):
                return CareerLevel.ENTRY
            return CareerLevel.MID

        return CareerLevel.UNKNOWN

    def infer_availability(self, notice_period: str | None) -> Availability:
        if not notice_period:
            return Availability.UNKNOWN
        lower = notice_period.lower().strip()
        if any(kw in lower.split() for kw in ("immediate", "immediately")) or "0 day" in lower.split():
            return Availability.IMMEDIATE
        if any(kw in lower for kw in ("1 week", "one week", "7 day")):
            return Availability.TWO_WEEKS
        if any(kw in lower for kw in ("2 week", "two week", "14 day", "15 day")):
            return Availability.TWO_WEEKS
        if any(kw in lower for kw in ("1 month", "one month", "30 day")):
            return Availability.ONE_MONTH
        if any(kw in lower for kw in ("2 month", "two month", "60 day")):
            return Availability.TWO_MONTHS
        if any(kw in lower for kw in ("3 month", "three month", "90 day")):
            return Availability.THREE_MONTHS
        if any(kw in lower for kw in ("notice", "serving")):
            return Availability.TWO_WEEKS
        return Availability.UNKNOWN

    def extract_industries(self, experiences: list) -> list[str]:
        industries: list[str] = []
        seen: set[str] = set()
        for exp in experiences:
            industry = getattr(exp, "industry", None) or ""
            if industry and industry.lower() not in seen:
                seen.add(industry.lower())
                industries.append(industry)
        return industries

    def extract_projects(self, projects: list) -> list[str]:
        names: list[str] = []
        for proj in projects:
            name = getattr(proj, "name", None) or ""
            if name:
                names.append(name)
        return names

    def extract_certifications(self, certs: list) -> list[str]:
        names: list[str] = []
        for cert in certs:
            name = getattr(cert, "name", None) or ""
            issuer = getattr(cert, "issuer", None) or ""
            if name and issuer:
                names.append(f"{name} ({issuer})")
            elif name:
                names.append(name)
        return names

    def extract_education_summary(self, education_list: list) -> str | None:
        if not education_list:
            return None
        highest = self._highest_degree(education_list)
        if highest:
            field = getattr(highest, "field_of_study", None) or ""
            institution = getattr(highest, "institution", None) or ""
            degree = getattr(highest, "degree", None) or ""
            if degree and field:
                return f"{degree} in {field} from {institution}" if institution else f"{degree} in {field}"
            if degree:
                return f"{degree} from {institution}" if institution else degree
        edu = education_list[0]
        field = getattr(edu, "field_of_study", None) or ""
        institution = getattr(edu, "institution", None) or ""
        if field and institution:
            return f"Studied {field} at {institution}"
        return institution or field or None

    def extract_languages(self, languages: list) -> list[LanguageInfo]:
        result: list[LanguageInfo] = []
        seen: set[str] = set()
        for lang in languages:
            name = (getattr(lang, "language", None) or "").strip().lower()
            if name and name not in seen:
                seen.add(name)
                proficiency = getattr(lang, "proficiency", None)
                result.append(
                    LanguageInfo(
                        language=getattr(lang, "language", ""),
                        proficiency=str(proficiency) if proficiency else None,
                    )
                )
        return result

    def extract_skill_names(self, skills: list) -> list[str]:
        return [getattr(s, "name", "") or "" for s in skills if getattr(s, "name", None)]

    def extract_years_of_experience(self, profile, experiences: list) -> float | None:
        if profile and getattr(profile, "total_years_experience", None) is not None:
            return float(profile.total_years_experience)
        return self._compute_years_from_experiences(experiences)

    def extract_salary_expectation(self, profile, preferences) -> str | None:
        if preferences and getattr(preferences, "minimum_salary", None) is not None:
            currency = getattr(preferences, "preferred_currency", "USD") or "USD"
            return f"{currency} {float(preferences.minimum_salary):,.0f}/year"
        if profile and getattr(profile, "expected_salary", None) is not None:
            return f"USD {float(profile.expected_salary):,.0f}/year"
        return None

    def extract_employment_preference(self, preferences) -> str | None:
        if not preferences:
            return None
        emp_types = getattr(preferences, "employment_types", None)
        if emp_types and isinstance(emp_types, list):
            return ", ".join(str(t).replace("_", " ").title() for t in emp_types)
        return None

    def extract_preferred_locations(self, preferences) -> list[str]:
        if not preferences:
            return []
        locs = getattr(preferences, "preferred_locations", None)
        if locs and isinstance(locs, list):
            return [str(loc) for loc in locs]
        return []

    def extract_remote_preference(self, preferences) -> bool | None:
        if not preferences:
            return None
        work_modes = getattr(preferences, "work_modes", None)
        if work_modes and isinstance(work_modes, list):
            modes = [str(m).lower().strip() for m in work_modes]
            if any(m in ("remote", "remote_only") for m in modes):
                return True
            if any(m in ("on_site", "onsite") for m in modes):
                return False
        return None

    def extract_strengths(
        self,
        skills: list,
        experiences: list,
    ) -> list[str]:
        strengths: list[str] = []
        seen: set[str] = set()
        for exp in experiences:
            achievements = getattr(exp, "achievements", None) or []
            if isinstance(achievements, list):
                for ach in achievements:
                    if isinstance(ach, str) and ach.strip():
                        summary = ach.strip()[:120]
                        if summary.lower() not in seen:
                            seen.add(summary.lower())
                            strengths.append(summary)
        for skill in skills:
            prof = getattr(skill, "proficiency", None)
            if prof and str(prof).lower() in ("expert", "advanced"):
                name = getattr(skill, "name", None)
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    strengths.append(f"Expert in {name}")
        return strengths[:10]

    def extract_career_goals(self, profile) -> str | None:
        if not profile:
            return None
        desired_role = getattr(profile, "desired_role", None)
        summary = getattr(profile, "professional_summary", None)
        if desired_role and summary:
            return f"Desired role: {desired_role}. {summary}"
        if desired_role:
            return f"Seeking a {desired_role} position"
        return summary

    def _normalize_skill(self, name: str) -> str:
        name = name.strip()
        lower = name.lower()
        canonical = SKILL_SYNONYMS.get(lower)
        if canonical:
            return canonical
        return name

    def _deduplicate_skills(self, names: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for name in names:
            lower = name.lower().strip()
            if lower and lower not in seen:
                seen.add(lower)
                result.append(name)
        return result

    def _skill_priority(
        self,
        skill: str,
        proficiencies: list[str | None],
        years_list: list[float | None],
    ) -> float:
        score = 1.0
        lower = skill.lower()
        for prof in proficiencies:
            if prof and str(prof).lower() in ("expert", "advanced"):
                score += 2.0
            elif prof and str(prof).lower() == "intermediate":
                score += 1.0
        for yrs in years_list:
            if yrs is not None:
                score += min(yrs / 5.0, 2.0)
        if lower in TECH_CLASSIFICATION:
            score += 0.5
        return score

    def _highest_degree(self, education_list: list):
        degree_order = [
            "phd",
            "doctorate",
            "ph.d.",
            "doctor",
            "master",
            "masters",
            "ms",
            "ma",
            "mba",
            "m.sc",
            "m.a.",
            "bachelor",
            "bachelors",
            "bs",
            "ba",
            "b.sc",
            "b.a.",
            "b.e.",
            "b.tech",
            "associate",
            "a.a.",
            "a.s.",
            "diploma",
            "certificate",
            "high school",
        ]
        best = None
        best_idx = len(degree_order)
        for edu in education_list:
            degree = (getattr(edu, "degree", None) or "").lower().strip()
            for i, keyword in enumerate(degree_order):
                if keyword in degree and i < best_idx:
                    best_idx = i
                    best = edu
                    break
        return best or (education_list[0] if education_list else None)

    def _compute_years_from_experiences(self, experiences: list) -> float | None:
        if not experiences:
            return None
        total_days = 0.0
        now = datetime.now(timezone.utc)
        for exp in experiences:
            start = getattr(exp, "start_date", None)
            if start is None:
                continue
            end = getattr(exp, "end_date", None)
            if end is None and not getattr(exp, "currently_working", False):
                continue
            if end is None:
                end = now
            if isinstance(start, datetime) and isinstance(end, datetime):
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                delta = end - start
                total_days += max(0.0, delta.total_seconds() / 86400.0)
        if total_days <= 0:
            return None
        return round(total_days / 365.0, 1)
