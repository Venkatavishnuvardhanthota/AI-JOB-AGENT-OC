from __future__ import annotations

import re

from app.job_matching.config import MatchingConfig
from app.job_matching.schemas import SkillMatchInfo


class SkillComparator:
    def __init__(self, config: MatchingConfig) -> None:
        self._config = config

    def compare(
        self,
        profile_skills: list[str],
        job_skills: list[str],
        profile_primary: list[str] | None = None,
        profile_secondary: list[str] | None = None,
    ) -> tuple[list[SkillMatchInfo], list[SkillMatchInfo], list[SkillMatchInfo], float]:
        profile_skills_lower = {s.lower().strip() for s in profile_skills}
        primary_lower = {s.lower().strip() for s in (profile_primary or [])}
        job_skills_lower = {s.lower().strip() for s in job_skills}

        matching: list[SkillMatchInfo] = []
        missing: list[SkillMatchInfo] = []
        preferred: list[SkillMatchInfo] = []

        matched_job = set()

        for js in job_skills:
            js_lower = js.lower().strip()
            is_found = js_lower in profile_skills_lower
            if is_found:
                matched_job.add(js_lower)
                matching.append(SkillMatchInfo(
                    name=js,
                    matched=True,
                    normalized_name=js,
                ))
            else:
                for ps in profile_skills:
                    ps_lower = ps.lower().strip()
                    if self._skills_related(ps_lower, js_lower):
                        matched_job.add(js_lower)
                        matching.append(SkillMatchInfo(
                            name=js,
                            matched=True,
                            normalized_name=ps,
                        ))
                        is_found = True
                        break
                if not is_found:
                    missing.append(SkillMatchInfo(
                        name=js,
                        matched=False,
                    ))

        for ps in profile_skills:
            ps_lower = ps.lower().strip()
            if ps_lower not in matched_job:
                category = "primary" if ps_lower in primary_lower else "secondary"
                preferred.append(SkillMatchInfo(
                    name=ps,
                    matched=False,
                    category=category,
                    normalized_name=ps,
                ))

        total = len(job_skills) or 1
        matched_count = len(matching)
        score = min(100.0, (matched_count / total) * 100.0)

        if profile_primary and job_skills:
            primary_in_job = sum(
                1 for s in profile_primary if s.lower().strip() in job_skills_lower
            )
            if primary_in_job >= len(profile_primary) * self._config.skills_min_match_percentage:
                score = min(100.0, score + self._config.skills_expert_bonus)

        return matching, missing, preferred, score


    @staticmethod
    def _skills_related(a: str, b: str) -> bool:
        return bool(a == b or a in b or b in a)


class ExperienceComparator:
    def compare(
        self,
        profile_years: float | None,
        job_experience_level: str | None,
        config: MatchingConfig,
    ) -> float:
        if profile_years is None and not job_experience_level:
            return 50.0

        if profile_years is None:
            return 30.0

        level_years: dict[str, tuple[float, float]] = {
            "entry": (0, 1),
            "junior": (1, 3),
            "mid": (3, 6),
            "senior": (6, 10),
            "lead": (10, 15),
            "executive": (15, 30),
        }

        if job_experience_level and job_experience_level.lower() in level_years:
            min_y, max_y = level_years[job_experience_level.lower()]
            mid = (min_y + max_y) / 2
            diff = abs(profile_years - mid)
            tolerance = config.experience_years_tolerance
            if diff <= tolerance:
                return 100.0
            if diff <= tolerance * 2:
                return 70.0
            if diff <= tolerance * 3:
                return 40.0
            return 20.0

        if profile_years >= 10:
            return 80.0
        if profile_years >= 5:
            return 60.0
        if profile_years >= 2:
            return 40.0
        return 20.0


class EducationComparator:
    DEGREE_ORDER: list[str] = [
        "phd", "doctorate", "ph.d.", "doctor",
        "master", "masters", "ms", "ma", "mba", "m.sc", "m.a.",
        "bachelor", "bachelors", "bs", "ba", "b.sc", "b.a.", "b.e.", "b.tech",
        "associate", "a.a.", "a.s.",
        "diploma",
        "certificate",
        "high school",
    ]

    def compare(self, profile_education: str | None, job_requirements: list[str] | None) -> float:
        if not profile_education and not job_requirements:
            return 50.0
        if not job_requirements:
            return 80.0
        if not profile_education:
            return 20.0

        profile_level = self._degree_level(profile_education)
        if profile_level is None:
            return 30.0

        required_levels = [
            self._degree_level(req)
            for req in job_requirements
            if self._degree_level(req) is not None
        ]
        if not required_levels:
            return 70.0

        max_required = max(required_levels)
        if profile_level >= max_required:
            return 100.0
        if profile_level >= max_required - 1:
            return 70.0
        return 30.0

    @classmethod
    def _degree_level(cls, text: str) -> int | None:
        lower = text.lower().strip()
        for i, keyword in enumerate(cls.DEGREE_ORDER):
            if keyword in lower:
                return len(cls.DEGREE_ORDER) - i
        return None


class LocationComparator:
    def compare(
        self,
        profile_locations: list[str] | None,
        job_city: str | None,
        job_state: str | None,
        job_country: str | None,
        job_display: str | None,
    ) -> float:
        if not profile_locations:
            return 50.0
        if not job_city and not job_state and not job_country and not job_display:
            return 60.0

        location_texts = [str(loc).lower().strip() for loc in profile_locations if loc]

        job_parts = []
        if job_city:
            job_parts.append(job_city.lower())
        if job_state:
            job_parts.append(job_state.lower())
        if job_country:
            job_parts.append(job_country.lower())
        if job_display:
            job_parts.append(job_display.lower())

        for lt in location_texts:
            for jp in job_parts:
                if lt == jp or lt in jp or jp in lt:
                    return 100.0

        if job_country and job_country.lower() in " ".join(location_texts):
            return 60.0

        return 20.0


class RemoteComparator:
    def compare(
        self,
        profile_remote: bool | None,
        job_remote_type: str | None,
    ) -> float:
        if profile_remote is None:
            return 50.0
        if not job_remote_type or job_remote_type == "unknown":
            return 60.0

        jt = job_remote_type.lower()
        if profile_remote:
            if jt == "remote":
                return 100.0
            if jt == "hybrid":
                return 70.0
            return 40.0
        if jt == "on_site":
            return 100.0
        if jt == "hybrid":
            return 70.0
        return 40.0


class SalaryComparator:
    def compare(
        self,
        profile_salary_str: str | None,
        job_salary_min: float | None,
        job_salary_max: float | None,
        config: MatchingConfig,
    ) -> float:
        if not profile_salary_str:
            return 50.0
        if job_salary_min is None and job_salary_max is None:
            return 60.0

        profile_amount = self._extract_salary_amount(profile_salary_str)
        if profile_amount is None:
            return 50.0

        if job_salary_min is not None and job_salary_max is not None:
            job_mid = (job_salary_min + job_salary_max) / 2
        elif job_salary_min is not None:
            job_mid = job_salary_min * 1.2
        elif job_salary_max is not None:
            job_mid = job_salary_max * 0.8
        else:
            return 60.0

        if job_mid <= 0:
            return 60.0

        diff = abs(profile_amount - job_mid) / job_mid
        tolerance = config.salary_tolerance_percentage
        if diff <= tolerance:
            return 100.0
        if diff <= tolerance * 2:
            return 70.0
        if diff <= tolerance * 3:
            return 40.0
        if profile_amount > job_mid:
            return 60.0
        return 20.0

    @staticmethod
    def _extract_salary_amount(text: str) -> float | None:
        match = re.search(r'([\d,.]+)', text.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None


class EmploymentTypeComparator:
    EMPLOYMENT_MAP: dict[str, list[str]] = {
        "full_time": ["full_time", "full-time", "full time", "permanent"],
        "part_time": ["part_time", "part-time", "part time"],
        "contract": ["contract", "contractor", "temporary"],
        "freelance": ["freelance", "freelancer", "self-employed"],
        "internship": ["internship", "intern", "trainee"],
    }

    def compare(
        self,
        profile_preference: str | None,
        job_type: str | None,
    ) -> float:
        if not profile_preference:
            return 50.0
        if not job_type or job_type == "other" or job_type == "unknown":
            return 60.0

        pref_lower = profile_preference.lower()
        job_lower = job_type.lower()

        for canonical, aliases in self.EMPLOYMENT_MAP.items():
            pref_match = canonical in pref_lower or any(a in pref_lower for a in aliases)
            job_match = canonical in job_lower or any(a in job_lower for a in aliases)
            if pref_match and job_match:
                return 100.0
            if pref_match or job_match:
                for alias in aliases:
                    if alias in pref_lower and alias in job_lower:
                        return 100.0

        return 20.0


class CareerLevelComparator:
    LEVEL_ORDER: list[str] = [
        "executive",
        "lead",
        "senior",
        "mid",
        "junior",
        "entry",
    ]

    def compare(self, profile_level: str | None, job_level: str | None) -> float:
        if not profile_level or profile_level == "unknown":
            return 50.0
        if not job_level or job_level == "unknown":
            return 60.0

        pl = profile_level.lower()
        jl = job_level.lower()

        if pl == jl:
            return 100.0

        try:
            p_idx = self.LEVEL_ORDER.index(pl)
            j_idx = self.LEVEL_ORDER.index(jl)
        except ValueError:
            return 50.0

        diff = abs(p_idx - j_idx)
        if diff == 1:
            return 70.0
        if diff == 2:
            return 40.0
        return 20.0


class IndustryComparator:
    def compare(
        self,
        profile_industries: list[str] | None,
        job_industry: str | None,
    ) -> float:
        if not profile_industries:
            return 50.0
        if not job_industry:
            return 60.0

        ji_lower = job_industry.lower().strip()
        for ind in profile_industries:
            ind_lower = ind.lower().strip()
            if ji_lower == ind_lower or ji_lower in ind_lower or ind_lower in ji_lower:
                return 100.0
        return 30.0


class CertificationsComparator:
    def compare(
        self,
        profile_certs: list[str] | None,
    ) -> float:
        if not profile_certs:
            return 30.0
        count = len(profile_certs)
        if count >= 5:
            return 100.0
        if count >= 3:
            return 80.0
        if count >= 1:
            return 60.0
        return 30.0


class ProjectsComparator:
    def compare(
        self,
        profile_projects: list[str] | None,
    ) -> float:
        if not profile_projects:
            return 20.0
        count = len(profile_projects)
        if count >= 5:
            return 100.0
        if count >= 3:
            return 75.0
        if count >= 1:
            return 50.0
        return 20.0
