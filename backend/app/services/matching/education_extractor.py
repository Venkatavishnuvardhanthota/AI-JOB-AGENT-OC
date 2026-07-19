import logging
import re

from app.models.education import Education
from app.schemas.matching import EducationScore

logger = logging.getLogger(__name__)

EDUCATION_LEVELS = {
    "phd": 5, "doctorate": 5, "ph.d": 5, "doctor": 5,
    "master": 4, "ms": 4, "ma": 4, "mba": 4, "m.tech": 4, "m.sc": 4, "m.a": 4,
    "bachelor": 3, "bs": 3, "ba": 3, "b.tech": 3, "b.sc": 3, "b.a": 3, "b.e": 3,
    "associate": 2, "a.a": 2, "a.s": 2,
    "high school": 1, "diploma": 1, "certificate": 1,
}

FIELD_KEYWORDS = {
    "computer science": ["computer science", "cs", "computing", "software"],
    "engineering": ["engineering", "engineer"],
    "data science": ["data science", "data", "analytics"],
    "information technology": ["information technology", "it", "information systems", "mis"],
    "mathematics": ["mathematics", "math", "statistics", "applied math"],
    "physics": ["physics", "physical"],
    "business": ["business", "business administration", "management", "finance", "economics"],
    "design": ["design", "graphic design", "ui/ux", "hci"],
    "biology": ["biology", "biochemistry", "bioinformatics", "biotech"],
    "electrical engineering": ["electrical engineering", "ee", "electronic"],
}

REQUIRED_LEVEL_PATTERN = re.compile(
    r'(?:bachelor|master|phd|ph\.d|doctorate|bs|ba|ms|ma|mba|b\.tech|m\.tech|'
    r'associate|high\s+school|diploma)(?:[\'"]?s)?(?:\s+(?:degree|in))?',
    re.IGNORECASE,
)


class EducationExtractor:
    def extract_required_level(self, text: str) -> str | None:
        if not text:
            return None
        match = REQUIRED_LEVEL_PATTERN.search(text)
        if match:
            raw = match.group(0).lower().strip()
            for level in sorted(EDUCATION_LEVELS, key=len, reverse=True):
                if level in raw:
                    return level
        return None

    def extract_required_field(self, text: str) -> str | None:
        if not text:
            return None
        lower = text.lower()
        for field, keywords in FIELD_KEYWORDS.items():
            for kw in keywords:
                if kw in lower:
                    return field
        return None

    def get_user_highest_level(self, educations: list[Education]) -> str:
        max_level = 0
        best = "unknown"
        for edu in educations:
            degree = (edu.degree or "").lower()
            for level_name, level_val in EDUCATION_LEVELS.items():
                if level_name in degree and level_val > max_level:
                    max_level = level_val
                    best = level_name
        return best

    def get_user_field(self, educations: list[Education]) -> str | None:
        for edu in educations:
            field = (edu.field_of_study or "").lower()
            for field_name, keywords in FIELD_KEYWORDS.items():
                for kw in keywords:
                    if kw in field:
                        return field_name
        return None

    def compute_score(
        self,
        educations: list[Education],
        job_description: str | None,
    ) -> EducationScore:
        user_level = self.get_user_highest_level(educations)
        required_level = self.extract_required_level(job_description or "")
        user_field = self.get_user_field(educations)
        required_field = self.extract_required_field(job_description or "")
        if required_level:
            user_lvl_val = EDUCATION_LEVELS.get(user_level, 0)
            req_lvl_val = EDUCATION_LEVELS.get(required_level, 3)
            level_match = user_lvl_val >= req_lvl_val
        else:
            level_match = True
        field_match = (user_field == required_field if user_field else False) if required_field else True
        score = 0.0
        if level_match and field_match:
            score = 1.0
        elif level_match or field_match:
            score = 0.6
        elif required_level or required_field:
            score = 0.2
        else:
            score = 0.5
        return EducationScore(
            user_level=user_level,
            required_level=required_level,
            user_field=user_field,
            required_field=required_field,
            level_match=level_match,
            field_match=field_match,
            score=round(score, 4),
        )
