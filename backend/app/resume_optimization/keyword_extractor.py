from __future__ import annotations

import re

from app.resume_optimization.schemas import KeywordAnalysis

TECH_STACK_CATEGORIES: dict[str, list[str]] = {
    "programming_languages": [
        "python",
        "javascript",
        "typescript",
        "java",
        "go",
        "rust",
        "c#",
        "c++",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "r",
        "dart",
        "sql",
        "html",
        "css",
        "bash",
        "shell",
        "powershell",
        "perl",
        "lua",
        "haskell",
        "elixir",
        "clojure",
    ],
    "frameworks": [
        "react",
        "angular",
        "vue",
        "django",
        "flask",
        "fastapi",
        "express",
        "node.js",
        "spring",
        "asp.net",
        "rails",
        "laravel",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "scikit-learn",
        "jquery",
        "bootstrap",
        "tailwind",
        "next.js",
        "nuxt",
        ".net",
        "dotnet",
    ],
    "databases": [
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "sqlite",
        "oracle",
        "mariadb",
        "cassandra",
        "dynamodb",
        "elasticsearch",
        "firebase",
        "bigquery",
        "snowflake",
        "cockroachdb",
        "neo4j",
        "influxdb",
    ],
    "cloud_platforms": [
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "docker",
        "kubernetes",
        "terraform",
        "jenkins",
        "heroku",
        "vercel",
        "netlify",
        "digitalocean",
    ],
    "tools": [
        "git",
        "github",
        "gitlab",
        "jira",
        "confluence",
        "slack",
        "figma",
        "tableau",
        "power bi",
        "grafana",
        "prometheus",
        "datadog",
        "kafka",
        "rabbitmq",
        "nginx",
        "ansible",
        "puppet",
        "chef",
        "circleci",
        "github actions",
        "gitlab ci",
        "agile",
        "scrum",
        "docker",
        "kubernetes",
        "jenkins",
    ],
}

SOFT_SKILLS: set[str] = {
    "leadership",
    "communication",
    "teamwork",
    "problem solving",
    "critical thinking",
    "time management",
    "project management",
    "analytical",
    "collaboration",
    "adaptability",
    "creativity",
    "mentoring",
    "presentation",
    "negotiation",
    "conflict resolution",
    "decision making",
    "strategic planning",
    "organization",
    "detail oriented",
    "self-motivated",
    "interpersonal",
    "verbal communication",
    "written communication",
    "cross-functional",
    "stakeholder management",
}


class KeywordExtractor:
    def extract(self, job_posting, match_result) -> KeywordAnalysis:
        required: list[str] = []
        preferred: list[str] = []
        technical: list[str] = []
        tools_list: list[str] = []
        soft: list[str] = []
        industry: list[str] = []

        job_skills = self._get_job_skills(job_posting)
        for skill in job_skills:
            lower = skill.lower().strip()
            cat = self._classify_tech(lower)
            if cat == "tools":
                tools_list.append(skill)
            elif cat:
                technical.append(skill)
            else:
                required.append(skill)

        if match_result:
            for ms in getattr(match_result, "matching_skills", []) or []:
                name = getattr(ms, "name", "") or ""
                if name and name not in required and name not in technical:
                    preferred.append(name)

            for ms in getattr(match_result, "preferred_skills", []) or []:
                name = getattr(ms, "name", "") or ""
                if name and name not in required and name not in technical:
                    preferred.append(name)

        desc = self._get_job_description(job_posting)
        if desc:
            desc_lower = desc.lower()
            for word in re.findall(r"\b[a-z]{3,}\b", desc_lower):
                if word in SOFT_SKILLS and word not in soft:
                    soft.append(word.title())

            industry_terms = self._extract_industry_terms(desc_lower)
            for term in industry_terms:
                if term not in industry:
                    industry.append(term)

        missing = [
            s
            for s in required
            if s.lower().strip() not in [x.lower().strip() for x in technical + tools_list + required]
        ]

        density = self._compute_keyword_density(desc or "", required + technical + tools_list)

        return KeywordAnalysis(
            required_keywords=required,
            preferred_keywords=preferred,
            technical_skills=technical,
            tools=tools_list,
            soft_skills=soft,
            industry_terms=industry,
            missing_required=missing,
            keyword_density=density,
        )

    @staticmethod
    def _classify_tech(skill: str) -> str | None:
        for category, keywords in TECH_STACK_CATEGORIES.items():
            for kw in keywords:
                if skill == kw:
                    return category
        return None

    @staticmethod
    def _extract_industry_terms(text: str) -> list[str]:
        terms: list[str] = []
        patterns = [
            r"\b(fintech|e[- ]?commerce|saas|healthcare|edtech|enterprise)\b",
            r"\b(blockchain|ai|machine learning|deep learning|data science|devops)\b",
            r"\b(agile|scrum|kanban|waterfall)\b",
            r"\b(b2b|b2c|d2c|marketplace|platform)\b",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                term = m.strip().title()
                if term not in terms:
                    terms.append(term)
        return terms

    @staticmethod
    def _compute_keyword_density(text: str, keywords: list[str]) -> float:
        if not text or not keywords:
            return 0.0
        words = text.split()
        if not words:
            return 0.0
        total = len(words)
        lower_words = [w.lower().strip(".,;:!?") for w in words]
        keyword_lower = [k.lower().strip() for k in keywords]
        matches = sum(1 for w in lower_words if w in keyword_lower)
        return round(matches / total, 4)

    @staticmethod
    def _get_job_skills(job_posting) -> list[str]:
        if not job_posting:
            return []
        return list(getattr(job_posting, "skills", []) or [])

    @staticmethod
    def _get_job_description(job_posting) -> str | None:
        if not job_posting:
            return None
        desc = getattr(job_posting, "description", None)
        if desc:
            return str(desc)
        return None
