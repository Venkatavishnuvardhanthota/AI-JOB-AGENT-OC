import logging
import re

from app.schemas.matching import SkillScore

logger = logging.getLogger(__name__)

TECH_SKILLS = {
    "python", "javascript", "typescript", "java", "c#", "c++", "c",
    "go", "golang", "rust", "swift", "kotlin", "ruby", "php", "scala",
    "perl", "r", "matlab", "sql", "nosql", "react", "angular", "vue",
    "node.js", "node", "express", "django", "flask", "fastapi", "spring",
    "asp.net", "rails", "laravel", "docker", "kubernetes", "k8s", "aws",
    "azure", "gcp", "terraform", "ansible", "jenkins", "git", "github",
    "gitlab", "ci/cd", "rest", "graphql", "grpc", "api", "redis",
    "mongodb", "postgresql", "mysql", "sqlite", "elasticsearch", "kafka",
    "rabbitmq", "machine learning", "deep learning", "nlp", "computer vision",
    "data science", "data engineering", "data analysis", "pytorch", "tensorflow",
    "pandas", "numpy", "scikit-learn", "tableau", "power bi", "excel",
    "linux", "unix", "bash", "powershell", "html", "css", "sass", "less",
    "webpack", "vite", "babel", "jest", "pytest", "junit", "selenium",
    "cypress", "playwright", "agile", "scrum", "jira", "confluence",
    "microservices", "serverless", "lambda", "ec2", "s3", "cloudfront",
    "oauth", "jwt", "saml", "ldap", "ssl", "tls", "networking", "tcp/ip",
    "dns", "http", "websocket", "restful", "soap", "xml", "json", "yaml",
    "toml", "vim", "vscode", "intellij", "eclipse", "postman", "swagger",
    "openapi", "nginx", "apache", "iis", "haproxy", "prometheus", "grafana",
    "datadog", "new relic", "splunk", "logstash", "filebeat", "fluentd",
    "hadoop", "spark", "airflow", "dbt", "snowflake", "bigquery", "redshift",
    "databricks", "sagemaker", "vertex ai", "mlflow", "kubeflow",
    "blockchain", "solidity", "web3", "ethereum", "smart contract",
    "ui/ux", "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "product management", "project management", "stakeholder", "leadership",
    "team management", "mentoring", "communication", "presentation",
}

EXPERIENCE_KEYWORDS = {
    "year of experience", "years of experience", "yr exp", "yrs exp",
    "years experience", "year experience", "experienced",
}


class SkillExtractor:
    def extract_from_text(self, text: str) -> list[str]:
        if not text:
            return []
        lower = text.lower()
        found = set()
        for skill in TECH_SKILLS:
            pattern = re.compile(r'\b' + re.escape(skill) + r'\b', re.IGNORECASE)
            if pattern.search(lower):
                found.add(skill)
        for match in re.finditer(r'(?:^|[\s,;.])([A-Z][a-z+#.]+(?:\s+[A-Z][a-z+#.]+)*)', text):
            candidate = match.group(1).strip().lower()
            if candidate in TECH_SKILLS:
                found.add(candidate)
        multi_word = [s for s in TECH_SKILLS if ' ' in s]
        for mw in multi_word:
            if mw in lower:
                found.add(mw)
        return sorted(found, key=lambda s: TECH_SKILLS_LIST_ORDER.get(s, 999))

    def extract_from_job(self, job: object) -> list[str]:
        skills = getattr(job, "skills", None) or []
        desc = getattr(job, "description", None) or ""
        extracted = self.extract_from_text(desc)
        combined = set(skills) | set(extracted)
        return sorted(combined)

    def compute_score(
        self, user_skills: list[str], job_skills: list[str]
    ) -> SkillScore:
        user_set = {s.lower().strip() for s in user_skills}
        job_set = {s.lower().strip() for s in job_skills}
        matched = sorted(job_set & user_set)
        missing = sorted(job_set - user_set)
        score = len(matched) / max(len(job_set), 1)
        return SkillScore(
            matched=[s.capitalize() for s in matched],
            missing=[s.capitalize() for s in missing],
            total_user=len(user_set),
            total_job=len(job_set),
            score=round(score, 4),
        )


TECH_SKILLS_LIST_ORDER = {s: i for i, s in enumerate(TECH_SKILLS)}
