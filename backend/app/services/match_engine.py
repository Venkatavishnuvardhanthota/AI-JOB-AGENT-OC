import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories import CareerProfileRepository, JobRepository
from app.services.audit import AuditService


class MatchEngineService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = JobRepository(session)
        self.profile_repo = CareerProfileRepository(session)
        self.audit_service = AuditService(session)

    async def calculate_score(self, user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found.")
        profile = await self.profile_repo.get_by_user(user_id)

        score = 50.0
        strengths = []
        skill_gaps = []
        summary = "Basic match analysis completed."

        if profile and profile.skills:
            profile_skill_names = {s.name.lower() for s in profile.skills}
            job_skills = self._extract_skills(job.description or "")
            matching = profile_skill_names & job_skills
            missing = job_skills - profile_skill_names
            strengths = list(matching)[:5]
            skill_gaps = list(missing)[:5]
            if job_skills:
                score = round((len(matching) / len(job_skills)) * 100, 1)
            summary = f"Matched {len(matching)} of {len(job_skills)} identified skills."

        result = {
            "score": score,
            "confidence": 0.7,
            "strengths": strengths,
            "skill_gaps": skill_gaps,
            "summary": summary,
        }
        await self.audit_service.log(
            "MATCH_CALCULATED",
            user_id=user_id,
            entity="job",
            entity_id=job_id,
            outcome="success",
        )
        return result

    def _extract_skills(self, description: str) -> set[str]:
        common_skills = {
            "python",
            "java",
            "javascript",
            "typescript",
            "react",
            "node.js",
            "fastapi",
            "django",
            "flask",
            "sql",
            "postgresql",
            "mongodb",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "git",
            "ci/cd",
            "machine learning",
            "deep learning",
            "nlp",
            "api",
            "rest",
            "graphql",
            "css",
            "html",
            "redis",
            "kafka",
            "rabbitmq",
        }
        desc_lower = description.lower()
        return {s for s in common_skills if s in desc_lower}
