from __future__ import annotations

import re

from app.application_intelligence.schemas import SkillExtraction

SKILL_CATEGORIES: dict[str, set[str]] = {
    "programming_languages": {
        "python", "javascript", "typescript", "java", "c#", "c++", "c",
        "ruby", "go", "golang", "rust", "swift", "kotlin", "scala",
        "php", "perl", "haskell", "elixir", "clojure", "dart",
        "sql", "bash", "shell", "powershell", "lua", "r",
    },
    "frameworks": {
        "react", "angular", "vue", "vue.js", "django", "flask", "fastapi",
        "spring", "spring boot", "express", "express.js", "next.js", "nuxt.js",
        "rails", "laravel", "asp.net", "asp.net core", "node.js", "nodejs",
        "tensorflow", "pytorch", "keras", "scikit-learn", "hadoop", "spark",
        "apache spark", "flink", "kafka", "rabbitmq", "grpc", "graphql",
        "redux", "jquery", "bootstrap", "tailwind", "sass", "less",
        "junit", "pytest", "jest", "mocha", "selenium", "cypress",
        ".net", ".net core", "entity framework", "hibernate", "mybatis",
        "struts", "play", "akka", "vert.x", "quarkus", "micronaut",
        "flutter", "react native", "xamarin", "electron",
    },
    "databases": {
        "postgresql", "postgres", "mysql", "sqlite", "mariadb",
        "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
        "couchdb", "neo4j", "influxdb", "timescaledb", "cockroachdb",
        "oracle", "sql server", "mssql", "db2", "snowflake",
        "bigquery", "redshift", "firestore", "realm",
    },
    "cloud_platforms": {
        "aws", "amazon web services", "azure", "google cloud", "gcp",
        "cloud", "kubernetes", "docker", "terraform", "ansible",
        "pulumi", "cloudformation", "jenkins", "circleci", "github actions",
        "gitlab ci", "travis ci", "heroku", "netlify", "vercel",
        "digitalocean", "linode", "vsphere", "openstack",
        "ecs", "eks", "ec2", "s3", "lambda", "cloudfront",
        "cloud run", "cloud functions", "app engine",
    },
    "developer_tools": {
        "git", "github", "gitlab", "bitbucket", "svn", "mercurial",
        "jira", "confluence", "trello", "asana", "notion",
        "vscode", "visual studio", "intellij", "eclipse", "vim", "emacs",
        "postman", "swagger", "openapi", "insomnia",
        "webpack", "vite", "rollup", "parcel", "gulp", "grunt",
        "babel", "eslint", "prettier", "sonarqube",
        "npm", "yarn", "pnpm", "pip", "maven", "gradle", "nuget",
        "cmake", "make", "gcc", "clang",
        "kibana", "grafana", "prometheus", "datadog", "new relic",
        "sentry", "logstash", "fluentd",
    },
    "soft_skills": {
        "leadership", "communication", "teamwork", "problem solving",
        "critical thinking", "time management", "mentoring", "collaboration",
        "analytical", "organizational", "adaptability", "creativity",
        "attention to detail", "self-motivated", "interpersonal",
        "presentation", "negotiation", "conflict resolution",
        "decision making", "strategic thinking", "emotional intelligence",
        "empathy", "patience", "curiosity", "growth mindset",
    },
}


class SkillExtractor:
    def extract(self, job_skills: list[str], description: str) -> SkillExtraction:
        raw = self._collect_raw_skills(job_skills, description)
        classified = self._classify(raw)
        classified.all_skills = sorted(raw)
        return classified

    def _collect_raw_skills(self, job_skills: list[str], description: str) -> set[str]:
        raw: set[str] = set()
        for skill in job_skills:
            raw.add(skill.lower().strip())

        desc_lower = description.lower()
        for _category, known_skills in SKILL_CATEGORIES.items():
            for skill in known_skills:
                if self._find_skill_in_text(skill, desc_lower):
                    raw.add(skill)
        return raw

    def _find_skill_in_text(self, skill: str, text: str) -> bool:
        pattern = re.compile(r'\b' + re.escape(skill) + r'\b', re.IGNORECASE)
        return bool(pattern.search(text))

    def _classify(self, raw: set[str]) -> SkillExtraction:
        result = SkillExtraction()
        assigned: set[str] = set()
        for category, known_skills in SKILL_CATEGORIES.items():
            for skill in raw:
                if skill in known_skills:
                    getattr(result, category).append(skill)
                    assigned.add(skill)

        for skill in raw:
            if skill not in assigned:
                result.developer_tools.append(skill)
                assigned.add(skill)
        return result
