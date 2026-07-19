"""Unit tests for the Phase 6 match scoring system."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.education import Education
from app.models.experience import Experience
from app.models.job_posting import JobPosting
from app.schemas.matching import (
    BatchScoreRequest,
    MatchScore,
    ScoringConfig,
    ScoringWeights,
)
from app.services.matching.company_analyzer import CompanyAnalyzer
from app.services.matching.education_extractor import EducationExtractor
from app.services.matching.experience_extractor import ExperienceExtractor
from app.services.matching.keyword_extractor import KeywordExtractor
from app.services.matching.scorer import MatchScorer
from app.services.matching.skill_extractor import SkillExtractor
from app.services.matching.threshold_filter import ThresholdFilter

# ── SkillExtractor ──


class TestSkillExtractor:
    def test_extract_from_text_python(self):
        ex = SkillExtractor()
        result = ex.extract_from_text("We need a Python developer with Django experience")
        assert "python" in result
        assert "django" in result

    def test_extract_from_text_empty(self):
        ex = SkillExtractor()
        assert ex.extract_from_text("") == []
        assert ex.extract_from_text(None) == []

    def test_extract_from_job_uses_both_skills_and_desc(self):
        ex = SkillExtractor()
        job = MagicMock(skills=["Python", "Docker"], description="Looking for React developer")
        result = ex.extract_from_job(job)
        assert "react" in result
        assert "Docker" in result

    def test_compute_score_perfect_match(self):
        ex = SkillExtractor()
        result = ex.compute_score(["Python", "Docker"], ["Python", "Docker"])
        assert result.score == 1.0
        assert len(result.matched) == 2
        assert len(result.missing) == 0

    def test_compute_score_partial(self):
        ex = SkillExtractor()
        result = ex.compute_score(["Python"], ["Python", "Docker", "Kubernetes"])
        assert 0.0 < result.score < 1.0
        assert len(result.matched) == 1
        assert len(result.missing) == 2

    def test_compute_score_no_match(self):
        ex = SkillExtractor()
        result = ex.compute_score(["Python"], ["Java", "C++"])
        assert result.score == 0.0

    def test_compute_score_no_job_skills(self):
        ex = SkillExtractor()
        result = ex.compute_score(["Python"], [])
        assert result.score == 0.0


# ── KeywordExtractor ──


class TestKeywordExtractor:
    def test_extract_removes_stopwords(self):
        ex = KeywordExtractor()
        result = ex.extract("the and a for with python developer")
        assert "python" in result
        assert "developer" in result

    def test_extract_empty(self):
        ex = KeywordExtractor()
        assert ex.extract("") == []
        assert ex.extract(None) == []

    def test_compute_score(self):
        ex = KeywordExtractor()
        result = ex.compute_score(["python", "docker"], ["python", "docker", "kubernetes"])
        assert result.score == pytest.approx(2 / 3, abs=0.001)
        assert len(result.matched) == 2

    def test_compute_score_no_match(self):
        ex = KeywordExtractor()
        result = ex.compute_score(["python"], ["java"])
        assert result.score == 0.0


# ── ExperienceExtractor ──


class TestExperienceExtractor:
    def test_extract_required_years(self):
        ex = ExperienceExtractor()
        assert ex.extract_required_years("5 years of experience required") == 5.0
        assert ex.extract_required_years("3+ years Python") == 3.0

    def test_extract_required_years_none(self):
        ex = ExperienceExtractor()
        assert ex.extract_required_years("No specific requirement") is None
        assert ex.extract_required_years("") is None

    def test_compute_user_years(self):
        ex = ExperienceExtractor()
        exps = [
            Experience(start_date=date(2020, 1, 1), end_date=date(2023, 1, 1), title="Engineer", company="Acme"),
        ]
        years = ex.compute_user_years(exps)
        assert years == pytest.approx(3.0, abs=0.1)

    def test_compute_user_years_no_experience(self):
        ex = ExperienceExtractor()
        assert ex.compute_user_years([]) == 0.0

    def test_compute_score_sufficient_experience(self):
        ex = ExperienceExtractor()
        exps = [Experience(start_date=date(2020, 1, 1), end_date=None, title="Software Engineer", company="Co")]
        with patch("app.services.matching.experience_extractor.ExperienceExtractor.compute_user_years") as mock_cuy:
            mock_cuy.return_value = 5.0
            result = ex.compute_score(exps, "Software Engineer", "5 years experience required")
            assert result.score > 0

    def test_compute_score_no_experience(self):
        ex = ExperienceExtractor()
        result = ex.compute_score([], "Software Engineer", "5 years experience")
        assert result.score == 0.0
        assert result.user_years == 0.0

    def test_extract_seniority(self):
        ex = ExperienceExtractor()
        assert ex.extract_seniority("Senior Engineer") == "senior"
        assert ex.extract_seniority("Junior Developer") == "junior"
        assert ex.extract_seniority("No seniority mentioned") == "senior"


# ── EducationExtractor ──


class TestEducationExtractor:
    def test_extract_required_level(self):
        ex = EducationExtractor()
        assert ex.extract_required_level("Bachelor's degree in Computer Science") is not None
        assert ex.extract_required_level("Master degree required") is not None
        assert ex.extract_required_level("No education requirement") is None

    def test_get_user_highest_level(self):
        ex = EducationExtractor()
        edus = [
            Education(degree="Bachelor of Science", institution="MIT", field_of_study="CS"),
        ]
        assert "bachelor" in ex.get_user_highest_level(edus)

    def test_get_user_highest_level_empty(self):
        ex = EducationExtractor()
        assert ex.get_user_highest_level([]) == "unknown"

    def test_compute_score_both_match(self):
        ex = EducationExtractor()
        edus = [Education(degree="Bachelor of Science", institution="MIT", field_of_study="Computer Science")]
        result = ex.compute_score(edus, "Bachelor's degree in Computer Science")
        assert result.score > 0.5

    def test_compute_score_no_education(self):
        ex = EducationExtractor()
        result = ex.compute_score([], "Bachelor's degree required")
        assert result.score == 0.2

    def test_get_user_field(self):
        ex = EducationExtractor()
        edus = [Education(degree="BS", institution="MIT", field_of_study="Computer Science")]
        assert ex.get_user_field(edus) is not None

    def test_get_user_field_empty(self):
        ex = EducationExtractor()
        assert ex.get_user_field([]) is None


# ── CompanyAnalyzer ──


class TestCompanyAnalyzer:
    def test_blacklisted_score_zero(self):
        ca = CompanyAnalyzer()
        result = ca.analyze("Acme Corp", ["Acme Corp"], [])
        assert result.is_blacklisted
        assert result.score == 0.0

    def test_previous_company_high_score(self):
        ca = CompanyAnalyzer()
        result = ca.analyze("Acme Corp", [], ["Acme Corp"])
        assert result.has_connections
        assert result.score > 0.5

    def test_neither_default_score(self):
        ca = CompanyAnalyzer()
        result = ca.analyze("Acme Corp", [], ["Other Corp"])
        assert not result.is_blacklisted
        assert not result.has_connections
        assert result.score == 0.5

    def test_case_insensitive_blacklist(self):
        ca = CompanyAnalyzer()
        result = ca.analyze("acme corp", ["Acme Corp"], [])
        assert result.is_blacklisted
        assert result.score == 0.0


# ── ThresholdFilter ──


class TestThresholdFilter:
    def test_above_all_thresholds(self):
        tf = ThresholdFilter()
        config = ScoringConfig()
        score = MatchScore(
            overall=0.8, skill__score=0.6, keyword__score=0.5,
            experience__score=0.7, education__score=0.5, company__score=0.5,
        )
        score.skill.score = 0.6
        score.keyword.score = 0.5
        score.experience.score = 0.7
        score.education.score = 0.5
        assert tf.is_above_threshold(score, config)

    def test_below_overall(self):
        tf = ThresholdFilter()
        config = ScoringConfig(overall_threshold=0.5)
        score = MatchScore(overall=0.3)
        score.skill.score = 0.6
        score.keyword.score = 0.5
        score.experience.score = 0.7
        score.education.score = 0.5
        assert not tf.is_above_threshold(score, config)

    def test_below_skill_threshold(self):
        tf = ThresholdFilter()
        config = ScoringConfig(skill_threshold=0.5)
        score = MatchScore(overall=0.8)
        score.skill.score = 0.2
        score.keyword.score = 0.5
        score.experience.score = 0.7
        score.education.score = 0.5
        assert not tf.is_above_threshold(score, config)

    def test_filter_scores(self):
        tf = ThresholdFilter()
        config = ScoringConfig()
        s1 = MatchScore(overall=0.9)
        s1.skill.score = 0.8
        s1.keyword.score = 0.7
        s1.experience.score = 0.8
        s1.education.score = 0.6
        s2 = MatchScore(overall=0.1)
        s2.skill.score = 0.1
        s2.keyword.score = 0.1
        s2.experience.score = 0.1
        s2.education.score = 0.1
        result = tf.filter_scores([s1, s2], config)
        assert len(result) == 1
        assert result[0].overall == 0.9


# ── MatchScorer ──


class TestMatchScorer:
    @pytest.mark.asyncio
    async def test_score_job_with_full_profile(self):
        session = AsyncMock(spec=AsyncSession)
        user_id = "user-1"

        mock_skill_result = MagicMock()
        mock_skill_result.scalars.return_value.all.return_value = [
            MagicMock(name="Python"),
            MagicMock(name="Docker"),
        ]

        mock_exp_result = MagicMock()
        mock_exp_result.scalars.return_value.all.return_value = [
            Experience(
                id="exp-1",
                user_id=user_id,
                company="PrevCo",
                title="Software Engineer",
                start_date=date(2020, 1, 1),
                end_date=date(2023, 1, 1),
                description="Built things",
            ),
        ]

        mock_edu_result = MagicMock()
        mock_edu_result.scalars.return_value.all.return_value = [
            Education(
                id="edu-1",
                user_id=user_id,
                institution="MIT",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
            ),
        ]

        mock_blacklist_result = MagicMock()
        mock_blacklist_result.scalars.return_value.all.return_value = []

        def execute_side_effect(stmt, **kw):

            stmt_str = str(stmt)
            if "skills" in stmt_str:
                return mock_skill_result
            if "experiences" in stmt_str:
                return mock_exp_result
            if "educations" in stmt_str:
                return mock_edu_result
            if "blacklisted" in stmt_str:
                return mock_blacklist_result
            return MagicMock()

        session.execute = AsyncMock(side_effect=execute_side_effect)

        job = JobPosting(
            id="job-1",
            title="Software Engineer",
            company_name="TechCo",
            description="Python developer with Docker experience. 3 years experience required.",
            skills=["Python", "Docker", "Kubernetes"],
            location="Remote",
            source="linkedin",
            content_hash="abc",
        )

        scorer = MatchScorer(session)
        result = await scorer.score_job(job, user_id)
        assert isinstance(result, MatchScore)
        assert 0 <= result.overall <= 1.0
        assert result.job_id == "job-1"
        assert result.scored_at is not None
        assert len(result.explanations) == 5

    @pytest.mark.asyncio
    async def test_score_job_empty_profile(self):
        session = AsyncMock(spec=AsyncSession)
        user_id = "user-empty"

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []

        def execute_side_effect(stmt, **kw):
            return empty_result

        session.execute = AsyncMock(side_effect=execute_side_effect)

        job = JobPosting(
            id="job-2",
            title="Senior Engineer",
            company_name="SomeCo",
            description="Requires 10 years experience, PhD preferred.",
            skills=["Java"],
            location="Office",
            source="indeed",
            content_hash="def",
        )

        scorer = MatchScorer(session)
        result = await scorer.score_job(job, user_id)
        assert result.overall < 0.5

    @pytest.mark.asyncio
    async def test_score_batch(self):
        session = AsyncMock(spec=AsyncSession)
        user_id = "user-batch"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = JobPosting(
            id="job-1", title="Engineer", company_name="Co",
            skills=["Python"], content_hash="h1", source="linkedin",
        )
        session.execute = AsyncMock(return_value=mock_result)

        req = BatchScoreRequest(job_ids=["job-1"])
        scorer = MatchScorer(session)
        with patch.object(scorer, "score_job") as mock_score:
            mock_score.return_value = MatchScore(overall=0.8, job_id="job-1")
            result = await scorer.score_batch(req, user_id)
        assert len(result.scores) == 1
        assert result.scores[0].overall == 0.8

    @pytest.mark.asyncio
    async def test_score_job_with_custom_config(self):
        session = AsyncMock(spec=AsyncSession)
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=empty_result)

        job = JobPosting(
            id="job-3",
            title="Engineer",
            company_name="Co",
            skills=["Python"],
            content_hash="h3",
            source="linkedin",
        )

        config = ScoringConfig(
            weights=ScoringWeights(skill=1.0, keyword=0.0, experience=0.0, education=0.0, company=0.0),
            overall_threshold=0.0,
            skill_threshold=0.0,
            keyword_threshold=0.0,
            experience_threshold=0.0,
            education_threshold=0.0,
        )

        scorer = MatchScorer(session)
        result = await scorer.score_job(job, "user-3", config)
        assert isinstance(result, MatchScore)
        assert result.explanations[0].weight == 1.0


# ── ScoringConfig Defaults ──


class TestScoringConfig:
    def test_default_weights_sum_to_one(self):
        weights = ScoringWeights()
        total = weights.skill + weights.keyword + weights.experience + weights.education + weights.company
        assert total == pytest.approx(1.0)

    def test_default_config_valid(self):
        config = ScoringConfig()
        assert 0.0 <= config.overall_threshold <= 1.0
        assert 0.0 <= config.skill_threshold <= 1.0


# ── MatchScore Serialization ──


class TestMatchScoreModel:
    def test_match_score_defaults(self):
        score = MatchScore()
        assert score.overall == 0.0
        assert score.skill.score == 0.0
        assert score.explanations == []

    def test_match_score_with_data(self):
        score = MatchScore(
            overall=0.85,
            skill__score=0.9,
            scored_at=datetime.now(timezone.utc),
            job_id="job-1",
        )
        score.skill.score = 0.9
        assert score.overall == 0.85
        assert score.job_id == "job-1"
