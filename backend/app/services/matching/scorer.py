import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blacklisted_company import BlacklistedCompany
from app.models.education import Education
from app.models.experience import Experience
from app.models.job_posting import JobPosting
from app.models.skill import Skill
from app.schemas.matching import (
    BatchScoreRequest,
    BatchScoreResponse,
    MatchScore,
    ScoreExplanation,
    ScoringConfig,
)
from app.services.matching.company_analyzer import CompanyAnalyzer
from app.services.matching.education_extractor import EducationExtractor
from app.services.matching.experience_extractor import ExperienceExtractor
from app.services.matching.keyword_extractor import KeywordExtractor
from app.services.matching.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = ScoringConfig()


class MatchScorer:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.skill_extractor = SkillExtractor()
        self.keyword_extractor = KeywordExtractor()
        self.experience_extractor = ExperienceExtractor()
        self.education_extractor = EducationExtractor()
        self.company_analyzer = CompanyAnalyzer()

    async def score_job(
        self,
        job: JobPosting,
        user_id: str,
        config: ScoringConfig | None = None,
    ) -> MatchScore:
        cfg = config or DEFAULT_CONFIG
        user_skills = await self._get_user_skills(user_id)
        experiences = await self._get_user_experiences(user_id)
        educations = await self._get_user_educations(user_id)
        blacklisted = await self._get_blacklisted_companies(user_id)
        user_company_names = [exp.company for exp in experiences]

        job_skills = self.skill_extractor.extract_from_job(job)
        skill_score = self.skill_extractor.compute_score(user_skills, job_skills)

        job_keywords = self.keyword_extractor.extract(
            (job.description or "") + " " + (job.title or "")
        )
        user_skill_keywords = user_skills + [
            exp.title for exp in experiences
        ]
        keyword_score = self.keyword_extractor.compute_score(
            user_skill_keywords, job_keywords
        )

        experience_score = self.experience_extractor.compute_score(
            experiences, job.title, job.description
        )

        education_score = self.education_extractor.compute_score(
            educations, job.description
        )

        company_score = self.company_analyzer.analyze(
            job.company_name, blacklisted, user_company_names
        )

        raw = (
            cfg.weights.skill * skill_score.score
            + cfg.weights.keyword * keyword_score.score
            + cfg.weights.experience * experience_score.score
            + cfg.weights.education * education_score.score
            + cfg.weights.company * company_score.score
        )

        if cfg.boost_exact_title_match:
            user_titles = [exp.title.lower() for exp in experiences if exp.title]
            if job.title and job.title.lower() in user_titles:
                raw = min(1.0, raw + 0.05)

        if cfg.boost_current_company:
            current = [
                exp for exp in experiences if exp.is_current and exp.company
            ]
            if current and job.company_name.lower() == current[0].company.lower():
                raw = min(1.0, raw + 0.05)

        if cfg.penalty_blacklisted and company_score.is_blacklisted:
            raw = max(0.0, raw - 0.3)

        overall = round(max(0.0, min(1.0, raw)), 4)

        explanations = [
            ScoreExplanation(
                category="skill",
                score=skill_score.score,
                weight=cfg.weights.skill,
                details=f"Matched {len(skill_score.matched)}/{skill_score.total_job} skills. "
                f"Missing: {', '.join(skill_score.missing[:5])}" if skill_score.missing
                else f"All {skill_score.total_job} job skills matched." if skill_score.total_job > 0
                else "No skills to compare.",
            ),
            ScoreExplanation(
                category="keyword",
                score=keyword_score.score,
                weight=cfg.weights.keyword,
                details=f"Matched {len(keyword_score.matched)}/{keyword_score.total} keywords.",
            ),
            ScoreExplanation(
                category="experience",
                score=experience_score.score,
                weight=cfg.weights.experience,
                details=(
                    f"User has {experience_score.user_years}y experience."
                    + (f" Job requires {experience_score.required_years}y."
                       if experience_score.required_years else "")
                    + (f" Relevant titles: {', '.join(experience_score.relevant_titles[:3])}"
                       if experience_score.relevant_titles
                       else " No directly relevant titles.")
                ),
            ),
            ScoreExplanation(
                category="education",
                score=education_score.score,
                weight=cfg.weights.education,
                details=f"User level: {education_score.user_level}"
                + (f", required: {education_score.required_level}." if education_score.required_level else ".")
                + (f" Field: {education_score.user_field or 'any'}." if education_score.user_field else ""),
            ),
            ScoreExplanation(
                category="company",
                score=company_score.score,
                weight=cfg.weights.company,
                details=f"Company: {company_score.company_name}."
                + (" Blacklisted." if company_score.is_blacklisted else "")
                + (" Previously worked here." if company_score.has_connections else ""),
            ),
        ]

        return MatchScore(
            overall=overall,
            skill=skill_score,
            keyword=keyword_score,
            experience=experience_score,
            education=education_score,
            company=company_score,
            explanations=explanations,
            scored_at=datetime.now(timezone.utc),
            job_id=str(job.id),
        )

    async def score_batch(
        self,
        req: BatchScoreRequest,
        user_id: str,
        config: ScoringConfig | None = None,
    ) -> BatchScoreResponse:
        scores = []
        for job_id in req.job_ids:
            stmt = select(JobPosting).where(JobPosting.id == job_id)
            result = await self.session.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                score = await self.score_job(job, user_id, config)
                scores.append(score)
        return BatchScoreResponse(scores=scores)

    async def _get_user_skills(self, user_id: str) -> list[str]:
        stmt = select(Skill).where(Skill.user_id == user_id)
        result = await self.session.execute(stmt)
        return [s.name for s in result.scalars().all()]

    async def _get_user_experiences(self, user_id: str) -> list[Experience]:
        stmt = (
            select(Experience)
            .where(Experience.user_id == user_id)
            .order_by(Experience.start_date.desc().nullslast())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _get_user_educations(self, user_id: str) -> list[Education]:
        stmt = (
            select(Education)
            .where(Education.user_id == user_id)
            .order_by(Education.start_date.desc().nullslast())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _get_blacklisted_companies(self, user_id: str) -> list[str]:
        stmt = select(BlacklistedCompany).where(BlacklistedCompany.user_id == user_id)
        result = await self.session.execute(stmt)
        return [b.company_name for b in result.scalars().all()]
