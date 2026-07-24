from __future__ import annotations

import re

from app.application_intelligence.config import ApplicationIntelligenceConfig
from app.application_intelligence.schemas import (
    RequirementAnalysis,
    ResponsibilityExtraction,
    RoleCategory,
    RoleIntelligence,
    RoleSeniority,
    SkillExtraction,
)

ROLE_CATEGORY_KEYWORDS: dict[RoleCategory, list[str]] = {
    RoleCategory.BACKEND: [
        "backend",
        "back-end",
        "back end",
        "server-side",
        "api",
        "microservice",
        "rest",
        "graphql",
        "database",
        "server",
        "middleware",
        "service-oriented",
    ],
    RoleCategory.FRONTEND: [
        "frontend",
        "front-end",
        "front end",
        "ui",
        "user interface",
        "ux",
        "react",
        "angular",
        "vue",
        "css",
        "html",
        "javascript",
        "typescript",
        "web design",
        "responsive design",
        "component",
    ],
    RoleCategory.FULL_STACK: [
        "full stack",
        "full-stack",
        "fullstack",
        "both frontend",
        "both front-end",
        "both back-end",
    ],
    RoleCategory.DATA_ANALYST: [
        "data analyst",
        "data analysis",
        "analytics",
        "tableau",
        "power bi",
        "looker",
        "excel",
        "sql",
        "reporting",
        "dashboard",
        "business intelligence",
    ],
    RoleCategory.DATA_SCIENTIST: [
        "data scientist",
        "data science",
        "machine learning",
        "statistical",
        "statistics",
        "modeling",
        "predictive",
        "nlp",
        "deep learning",
        "neural network",
        "regression",
        "classification",
        "clustering",
    ],
    RoleCategory.ML_ENGINEER: [
        "ml engineer",
        "machine learning engineer",
        "mlops",
        "model deployment",
        "training pipeline",
        "model serving",
        "feature engineering",
        "tensorflow",
        "pytorch",
        "model training",
    ],
    RoleCategory.DEVOPS: [
        "devops",
        "dev-ops",
        "site reliability",
        "sre",
        "infrastructure",
        "ci/cd",
        "cicd",
        "continuous integration",
        "deployment",
        "kubernetes",
        "docker",
        "terraform",
        "ansible",
        "jenkins",
        "cloud infrastructure",
        "platform engineer",
    ],
    RoleCategory.CLOUD: [
        "cloud engineer",
        "cloud architect",
        "cloud infrastructure",
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "cloud migration",
    ],
    RoleCategory.QA: [
        "qa",
        "quality assurance",
        "test engineer",
        "testing",
        "automation test",
        "manual test",
        "selenium",
        "cypress",
        "integration test",
        "e2e test",
        "regression test",
    ],
    RoleCategory.MOBILE: [
        "mobile",
        "ios",
        "android",
        "swift",
        "kotlin",
        "react native",
        "flutter",
        "mobile app",
        "ipad",
        "iphone",
    ],
    RoleCategory.UI_UX: [
        "ui/ux",
        "ux designer",
        "ui designer",
        "user research",
        "wireframe",
        "prototype",
        "figma",
        "sketch",
        "adobe xd",
        "interaction design",
        "visual design",
    ],
    RoleCategory.CYBER_SECURITY: [
        "security",
        "cyber",
        "cybersecurity",
        "cyber security",
        "information security",
        "infosec",
        "penetration testing",
        "vulnerability",
        "compliance",
        "security engineer",
    ],
}

SENIORITY_KEYWORDS: dict[RoleSeniority, list[str]] = {
    RoleSeniority.ENTRY: ["junior", "entry", "entry-level", "graduate", "trainee", "intern", "fresher", "associate"],
    RoleSeniority.MID: ["mid", "mid-level", "midlevel", "intermediate", "staff"],
    RoleSeniority.SENIOR: ["senior", "sr", "sr.", "lead", "principal", "staff engineer", "architect"],
    RoleSeniority.EXECUTIVE: [
        "vp",
        "vice president",
        "director",
        "head of",
        "chief",
        "cto",
        "ceo",
        "vice-president",
    ],
}

RESPONSIBILITY_PATTERNS: dict[str, list[str]] = {
    "primary": [
        r"responsible for (developing|building|designing|implementing|maintaining|managing)",
        r"(develop|build|design|implement|maintain|manage|lead|own) (.+?)(?:\.|;|$)",
        r"primary (responsibility|focus) (?:is|includes?) (.+?)(?:\.|;|$)",
        r"(?:role|position) (?:involves|includes?) (.+?)(?:\.|;|$)",
    ],
    "secondary": [
        r"(?:participate|participating) in (.+?)(?:\.|;|$)",
        r"(?:assist|support) (.+?)(?:\.|;|$)",
        r"(?:help|helping) (.+?)(?:\.|;|$)",
        r"contribut(?:e|ing) to (.+?)(?:\.|;|$)",
    ],
    "leadership": [
        r"(lead|leading|manage|managing) a team",
        r"(mentor|coach|guide) (?:junior|team|developer)",
        r"(leadership|team lead|tech lead|engineering manager)",
        r"(oversee|direct|supervise)",
    ],
    "communication": [
        r"communicat(?:e|ion|ing) (?:with|across|between)",
        r"(collaborate|coordinate|partner) (?:with|across|between)",
        r"stakeholder (?:management|communication)",
        r"(present|presenting) (?:to|findings|results)",
    ],
    "customer_facing": [
        r"(?:work with|collaborate with|interface with) (?:client|customer|stakeholder)",
        r"client[- ]facing",
        r"customer[- ]facing",
        r"(?:gather|understand|translate) (?:client|customer|business) requirement",
    ],
    "mentoring": [
        r"(mentor|mentoring) (?:junior|team|engineer|developer)",
        r"(coach|coaching) (?:junior|team|engineer)",
        r"(guide|develop) (?:junior|team) member",
        r"(code review|providing feedback|knowledge sharing)",
    ],
}

SENIORITY_ORDER = {
    RoleSeniority.ENTRY: 0,
    RoleSeniority.JUNIOR: 0,
    RoleSeniority.MID: 1,
    RoleSeniority.SENIOR: 2,
    RoleSeniority.LEAD: 3,
    RoleSeniority.EXECUTIVE: 4,
    RoleSeniority.UNKNOWN: -1,
}


class RoleAnalyzer:
    def __init__(self, config: ApplicationIntelligenceConfig) -> None:
        self._config = config

    def analyze(self, job, skills: SkillExtraction) -> RoleIntelligence:
        result = RoleIntelligence()
        if not job:
            return result

        title = getattr(job, "title", None) or ""
        description = getattr(job, "description", None) or ""
        full_text = f"{title} {description}".lower()

        result.summary = title or None
        result.seniority = self._infer_seniority(full_text, job)
        result.category = self._classify_role(full_text, skills)
        result.skills = skills
        result.responsibilities = self._extract_responsibilities(full_text)
        result.qualifications = self._extract_qualifications(full_text)
        result.education_requirements = self._extract_education_requirements(full_text)
        result.certification_requirements = self._extract_certification_requirements(full_text)
        result.travel_requirements = self._extract_travel_requirements(full_text)
        result.visa_sponsorship_mentioned = self._check_visa_sponsorship(full_text)
        return result

    def _infer_seniority(self, full_text: str, job) -> RoleSeniority:
        level = getattr(job, "experience_level", None)
        if level:
            level_str = str(level).lower()
            if level_str in ("entry", "junior"):
                return RoleSeniority.JUNIOR
            if level_str == "mid":
                return RoleSeniority.MID
            if level_str == "senior":
                return RoleSeniority.SENIOR
            if level_str == "lead":
                return RoleSeniority.LEAD
            if level_str == "executive":
                return RoleSeniority.EXECUTIVE

        matched: list[tuple[RoleSeniority, int]] = []
        for seniority, keywords in SENIORITY_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_text, re.IGNORECASE):
                    matched.append((seniority, SENIORITY_ORDER.get(seniority, -1)))
                    break

        if not matched:
            return RoleSeniority.UNKNOWN

        matched.sort(key=lambda x: x[1], reverse=True)
        return matched[0][0]

    def _classify_role(self, full_text: str, skills: SkillExtraction) -> RoleCategory:
        scores: dict[RoleCategory, int] = {cat: 0 for cat in RoleCategory}

        for category, keywords in ROLE_CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", full_text, re.IGNORECASE):
                    scores[category] = scores.get(category, 0) + 2

        if skills.programming_languages:
            has_frontend = any(
                lang in {"javascript", "typescript", "html", "css"} for lang in skills.programming_languages
            )
            has_backend = any(
                lang in {"python", "java", "c#", "go", "ruby", "php", "rust", "scala"}
                for lang in skills.programming_languages
            )
            if has_frontend and has_backend:
                scores[RoleCategory.FULL_STACK] = scores.get(RoleCategory.FULL_STACK, 0) + 3
            elif has_frontend:
                scores[RoleCategory.FRONTEND] = scores.get(RoleCategory.FRONTEND, 0) + 2
            elif has_backend:
                scores[RoleCategory.BACKEND] = scores.get(RoleCategory.BACKEND, 0) + 2

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return RoleCategory.GENERAL_SOFTWARE_ENGINEER
        return best

    def _extract_responsibilities(self, full_text: str) -> ResponsibilityExtraction:
        result = ResponsibilityExtraction()
        for category, patterns in RESPONSIBILITY_PATTERNS.items():
            found: list[str] = []
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for m in matches:
                    if isinstance(m, tuple):
                        m = " ".join(part for part in m if part)
                    text = m.strip().rstrip(".,;")
                    if text and text not in found:
                        found.append(text)
            if found:
                getattr(result, category).extend(found[:5])
        return result

    def _extract_qualifications(self, full_text: str) -> RequirementAnalysis:
        result = RequirementAnalysis()

        required_patterns = [
            r"(?:must have|required|requirement|requires|need|minimum|essential|necessary)"
            r"\s*(?:[:\-]?\s*)(.+?)(?:\.|;|$)",
            r"(?:must|should) (?:be able to|have|possess|demonstrate) (.+?)(?:\.|;|$)",
        ]
        preferred_patterns = [
            r"(?:preferred|prefer|nice to have|plus|bonus|desirable|ideal(?:ly)?)\s*(?:[:\-]?\s*)(.+?)(?:\.|;|$)",
            r"(?:would be|is a)\s+(a plus|a bonus|plus|preferred|desirable|nice to have)\s+(.+?)(?:\.|;|$)",
        ]

        seen_required: set[str] = set()
        for pattern in required_patterns:
            for m in re.finditer(pattern, full_text, re.IGNORECASE):
                if m.lastindex and m.lastindex >= 1:
                    text = m.group(1).strip().rstrip(".,;")
                    if text and text not in seen_required:
                        result.required.append(text)
                        seen_required.add(text)

        seen_preferred: set[str] = set()
        for pattern in preferred_patterns:
            for m in re.finditer(pattern, full_text, re.IGNORECASE):
                if m.lastindex and m.lastindex >= 1:
                    text = m.group(1).strip().rstrip(".,;")
                    if text and text not in seen_preferred:
                        result.preferred.append(text)
                        seen_preferred.add(text)

        return result

    def _extract_education_requirements(self, full_text: str) -> list[str]:
        result: list[str] = []
        edu_patterns = [
            r"(?:bachelor|master|phd|ph\.d|b\.s|m\.s|b\.a|m\.a|bs\s+in|ms\s+in|ba\s+in|ma\s+in)\s*(?:'s|\s+degree)?(?:\s+in\s+)?(\w+(?:\s+\w+)?)",
            r"(?:degree|education)\s*(?:in|:)?\s*(.+?)(?:\.|;|$|or)",
        ]
        seen: set[str] = set()
        for pattern in edu_patterns:
            for m in re.finditer(pattern, full_text, re.IGNORECASE):
                text = m.group(0).strip().rstrip(".,;")
                if text and text not in seen:
                    result.append(text)
                    seen.add(text)
        return result[:3]

    def _extract_certification_requirements(self, full_text: str) -> list[str]:
        result: list[str] = []
        cert_patterns = [
            r"(?:certification|certified|certificate)\s*(?:in|:)?\s*(.+?)(?:\.|;|$)",
        ]
        seen: set[str] = set()
        for pattern in cert_patterns:
            for m in re.finditer(pattern, full_text, re.IGNORECASE):
                text = m.group(0).strip().rstrip(".,;")
                if text and text not in seen:
                    result.append(text)
                    seen.add(text)
        return result[:3]

    def _extract_travel_requirements(self, full_text: str) -> str | None:
        travel_patterns = [
            r"(?:travel|willing to travel|ability to travel|requires travel)\s*(.+?)(?:\.|;|$)",
            r"(?:some|occasional|frequent|minimal|up to \d+%) travel",
        ]
        for pattern in travel_patterns:
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                return m.group(0).strip().rstrip(".,;")
        return None

    def _check_visa_sponsorship(self, full_text: str) -> bool | None:
        must_sponsor = re.search(
            r"(?:visa sponsorship|\bsponsor\b|h1b|h-1b|work visa|visa transfer)",
            full_text,
            re.IGNORECASE,
        )
        no_sponsor = re.search(
            r"(?:no sponsorship|cannot sponsor|unable to sponsor|no visa" r"|must have work authorization)",
            full_text,
            re.IGNORECASE,
        )
        if must_sponsor:
            return True
        if no_sponsor:
            return False
        return None
