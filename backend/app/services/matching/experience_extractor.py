import contextlib
import logging
import re

from app.models.experience import Experience
from app.schemas.matching import ExperienceScore

logger = logging.getLogger(__name__)

RELEVANT_TITLE_KEYWORDS = [
    "engineer", "developer", "architect", "lead", "manager", "director",
    "head", "sde", "swe", "backend", "frontend", "fullstack", "full stack",
    "data", "ml", "ai", "machine learning", "deep learning", "devops",
    "infrastructure", "platform", "site reliability", "sre", "security",
    "analyst", "scientist", "researcher", "consultant", "specialist",
    "technical", "software", "system", "integration", "test", "qa",
    "automation", "product", "program", "project",
]

YEAR_PATTERN = re.compile(
    r'(\d+)\s*[-–+to]?\s*(\d+)?\s*(?:year|yr|years|yrs)',
    re.IGNORECASE,
)
SENIORITY_PATTERN = re.compile(
    r'(senior|junior|mid[\s-]level|entry[\s-]level|associate|lead|principal|staff|intern)',
    re.IGNORECASE,
)


class ExperienceExtractor:
    def extract_required_years(self, text: str) -> float | None:
        if not text:
            return None
        matches = YEAR_PATTERN.findall(text)
        if not matches:
            return None
        years = []
        for a, b in matches:
            if b:
                with contextlib.suppress(ValueError):
                    years.append((int(a) + int(b)) / 2.0)
            else:
                with contextlib.suppress(ValueError):
                    years.append(float(a))
        return max(years) if years else None

    def extract_seniority(self, text: str) -> str | None:
        if not text:
            return None
        match = SENIORITY_PATTERN.search(text)
        return match.group(1).lower() if match else None

    def compute_user_years(self, experiences: list[Experience]) -> float:
        total = 0.0
        from datetime import date
        for exp in experiences:
            if exp.start_date:
                end = exp.end_date or date.today()
                delta = (end - exp.start_date).days / 365.25
                total += max(0, delta)
        return round(total, 1)

    def compute_score(
        self,
        experiences: list[Experience],
        job_title: str,
        job_description: str | None,
    ) -> ExperienceScore:
        user_years = self.compute_user_years(experiences)
        required_years = self.extract_required_years(job_description or "")
        relevant_titles = [
            exp.title for exp in experiences
            if any(kw in (exp.title or "").lower() for kw in RELEVANT_TITLE_KEYWORDS)
        ]
        has_relevant = len(relevant_titles) > 0
        required = required_years if required_years else 0.0
        if required > 0:
            score = min(1.0, user_years / required)
        elif has_relevant:
            score = 0.8
        else:
            score = 0.3
        score = round(max(0.0, min(1.0, score)), 4)
        return ExperienceScore(
            user_years=user_years,
            required_years=required_years,
            has_relevant=has_relevant,
            relevant_titles=relevant_titles,
            score=score,
        )
