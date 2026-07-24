import pytest
import structlog

from app.intelligence.analytics import AnalyticsEngine
from app.intelligence.config import IntelligenceConfig
from app.intelligence.dependencies import get_intelligence_service, reset_intelligence_service
from app.intelligence.exceptions import (
    AnalyticsDataError,
    ExperimentDataError,
    OptimizationDataError,
    RecommendationDataError,
    ScoringError,
)
from app.intelligence.experiments import ExperimentEngine
from app.intelligence.feedback import FeedbackProcessor
from app.intelligence.history import IntelligenceHistory
from app.intelligence.learning import LearningEngine
from app.intelligence.optimization import OptimizationEngine
from app.intelligence.recommendations import RecommendationEngine
from app.intelligence.scoring import ScoringEngine
from app.intelligence.service import IntelligenceService

logger = structlog.get_logger(__name__)


@pytest.fixture
def config() -> IntelligenceConfig:
    return IntelligenceConfig(
        min_data_points_for_analytics=1,
        min_data_points_for_recommendations=1,
        min_data_points_for_learning=1,
        min_data_points_for_optimization=1,
        experiment_sample_size_target=2,
    )


@pytest.fixture
def analytics(config: IntelligenceConfig) -> AnalyticsEngine:
    return AnalyticsEngine(config)


@pytest.fixture
def recommendations(config: IntelligenceConfig) -> RecommendationEngine:
    return RecommendationEngine(config)


@pytest.fixture
def learning(config: IntelligenceConfig) -> LearningEngine:
    return LearningEngine(config)


@pytest.fixture
def optimization(config: IntelligenceConfig) -> OptimizationEngine:
    return OptimizationEngine(config)


@pytest.fixture
def scoring(config: IntelligenceConfig) -> ScoringEngine:
    return ScoringEngine(config)


@pytest.fixture
def feedback(config: IntelligenceConfig) -> FeedbackProcessor:
    return FeedbackProcessor(config)


@pytest.fixture
def history(config: IntelligenceConfig) -> IntelligenceHistory:
    return IntelligenceHistory(config)


@pytest.fixture
def experiments(config: IntelligenceConfig) -> ExperimentEngine:
    return ExperimentEngine(config)


@pytest.fixture
def service(
    config: IntelligenceConfig,
    analytics: AnalyticsEngine,
    recommendations: RecommendationEngine,
    learning: LearningEngine,
    optimization: OptimizationEngine,
    scoring: ScoringEngine,
    feedback: FeedbackProcessor,
    history: IntelligenceHistory,
    experiments: ExperimentEngine,
) -> IntelligenceService:
    return IntelligenceService(
        config=config,
        analytics=analytics,
        recommendations=recommendations,
        learning=learning,
        optimization=optimization,
        scoring=scoring,
        feedback=feedback,
        history=history,
        experiments=experiments,
    )


def sample_applications() -> list[dict]:
    return [
        {
            "status": "success",
            "provider": "linkedin",
            "resume_id": "resume_1",
            "cover_letter_id": "cl_1",
            "source": "linkedin",
            "industry": "tech",
            "company": "Acme Corp",
            "location": "San Francisco",
            "salary": 120000,
            "response_time_days": 5,
        },
        {
            "status": "success",
            "provider": "linkedin",
            "resume_id": "resume_1",
            "cover_letter_id": "cl_1",
            "source": "linkedin",
            "industry": "tech",
            "company": "Beta Inc",
            "location": "San Francisco",
            "salary": 135000,
            "response_time_days": 3,
        },
        {
            "status": "rejected",
            "provider": "indeed",
            "resume_id": "resume_2",
            "cover_letter_id": "cl_2",
            "source": "indeed",
            "industry": "finance",
            "company": "Gamma LLC",
            "location": "New York",
            "salary": 110000,
            "response_time_days": 10,
        },
        {
            "status": "success",
            "provider": "linkedin",
            "resume_id": "resume_1",
            "cover_letter_id": "cl_1",
            "source": "linkedin",
            "industry": "tech",
            "company": "Delta Co",
            "location": "Remote",
            "salary": 140000,
            "response_time_days": 7,
        },
        {
            "status": "rejected",
            "provider": "indeed",
            "resume_id": "resume_2",
            "cover_letter_id": "cl_2",
            "source": "indeed",
            "industry": "finance",
            "company": "Epsilon Ltd",
            "location": "New York",
            "salary": 105000,
            "response_time_days": 14,
        },
    ]


# ── Analytics Tests ──


class TestAnalytics:
    async def test_analyze_empty_data_raises(self, analytics: AnalyticsEngine) -> None:
        with pytest.raises(AnalyticsDataError):
            await analytics.analyze([])

    async def test_analyze_full(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.analyze(data)
        assert result["total_applications"] == 5
        assert result["application_success_rate"]["rate"] == 0.6
        assert result["application_success_rate"]["percentage"] == 60.0

    async def test_application_success_rate(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.application_success_rate(data)
        assert result["successful"] == 3
        assert result["total"] == 5
        assert result["rate"] == 0.6

    async def test_provider_success_rate(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.provider_success_rate(data)
        linkedin = next(r for r in result if r["provider"] == "linkedin")
        indeed = next(r for r in result if r["provider"] == "indeed")
        assert linkedin["rate"] == 1.0
        assert indeed["rate"] == 0.0

    async def test_resume_effectiveness(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.resume_effectiveness(data)
        assert result["best_resume"]["resume_id"] == "resume_1"
        assert result["best_resume"]["rate"] == 1.0
        assert result["average_rate"] == 0.5

    async def test_cover_letter_effectiveness(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.cover_letter_effectiveness(data)
        assert result["best_cover_letter"]["cover_letter_id"] == "cl_1"
        assert result["best_cover_letter"]["rate"] == 1.0

    async def test_job_source_effectiveness(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.job_source_effectiveness(data)
        linkedin = next(r for r in result if r["source"] == "linkedin")
        indeed = next(r for r in result if r["source"] == "indeed")
        assert linkedin["rate"] == 1.0
        assert indeed["rate"] == 0.0

    async def test_salary_trends(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.salary_trends(data)
        avg = next(r for r in result if r["metric"] == "average")
        assert avg["value"] == 122000.0

    async def test_location_trends(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.location_trends(data)
        sf = next(r for r in result if r["location"] == "San Francisco")
        ny = next(r for r in result if r["location"] == "New York")
        assert sf["count"] == 2
        assert ny["count"] == 2

    async def test_industry_trends(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.industry_trends(data)
        tech = next(r for r in result if r["industry"] == "tech")
        finance = next(r for r in result if r["industry"] == "finance")
        assert tech["count"] == 3
        assert finance["count"] == 2

    async def test_company_trends(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.company_trends(data)
        acme = next(r for r in result if r["company"] == "Acme Corp")
        assert acme["count"] == 1

    async def test_response_time(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.response_time(data)
        assert result["average_days"] == pytest.approx(7.8, rel=0.1)
        assert result["min_days"] == 3
        assert result["max_days"] == 14

    async def test_acceptance_rate(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.acceptance_rate(data)
        assert result["accepted"] == 0
        assert result["rate"] == 0.0

    async def test_rejection_rate(self, analytics: AnalyticsEngine) -> None:
        data = sample_applications()
        result = await analytics.rejection_rate(data)
        assert result["rejected"] == 2
        assert result["rate"] == 0.4

    async def test_acceptance_rate_success(self, analytics: AnalyticsEngine) -> None:
        data = [
            {"status": "accepted"},
            {"status": "rejected"},
            {"status": "offer"},
        ]
        result = await analytics.acceptance_rate(data)
        assert result["accepted"] == 2
        assert result["rate"] == pytest.approx(0.6667, rel=0.01)

    async def test_empty_salary_trends(self, analytics: AnalyticsEngine) -> None:
        result = await analytics.salary_trends([{"status": "success"}])
        assert result == []


# ── Recommendation Tests ──


class TestRecommendations:
    async def test_best_resume(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"resume_id": "r1", "status": "success"},
            {"resume_id": "r1", "status": "success"},
            {"resume_id": "r2", "status": "rejected"},
        ]
        result = await recommendations.best_resume(history)
        assert result["recommended_value"] == "r1"
        assert result["confidence"] == 1.0

    async def test_best_resume_insufficient_data(self, recommendations: RecommendationEngine) -> None:
        with pytest.raises(RecommendationDataError):
            await recommendations.best_resume([])

    async def test_best_cover_letter(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"cover_letter_id": "cl1", "status": "success"},
            {"cover_letter_id": "cl1", "status": "rejected"},
            {"cover_letter_id": "cl2", "status": "success"},
        ]
        result = await recommendations.best_cover_letter(history)
        assert result["recommended_value"] == "cl1" or result["recommended_value"] == "cl2"

    async def test_best_provider(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"provider": "p1", "status": "success"},
            {"provider": "p1", "status": "success"},
            {"provider": "p2", "status": "rejected"},
        ]
        result = await recommendations.best_provider(history)
        assert result["recommended_value"] == "p1"

    async def test_best_strategy(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"strategy": "manual", "status": "success"},
            {"strategy": "manual", "status": "success"},
            {"strategy": "auto", "status": "rejected"},
        ]
        result = await recommendations.best_strategy(history)
        assert result["recommended_value"] == "manual"

    async def test_best_timing(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"hour": 9, "status": "success"},
            {"hour": 9, "status": "success"},
            {"hour": 14, "status": "rejected"},
        ]
        result = await recommendations.best_timing(history)
        assert result["recommended_value"] == "09:00"

    async def test_best_ai_model(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"ai_model": "gpt-4", "status": "success", "quality": 0.9},
            {"ai_model": "gpt-4", "status": "success", "quality": 0.8},
            {"ai_model": "claude", "status": "rejected", "quality": 0.5},
        ]
        result = await recommendations.best_ai_model(history)
        assert result["recommended_value"] == "gpt-4"

    async def test_best_prompt_template(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"prompt_template": "template_a", "status": "success", "cost": 0.01, "latency": 100},
            {"prompt_template": "template_a", "status": "success", "cost": 0.02, "latency": 200},
            {"prompt_template": "template_b", "status": "rejected", "cost": 0.05, "latency": 500},
        ]
        result = await recommendations.best_prompt_template(history)
        assert result["recommended_value"] == "template_a"

    async def test_best_retry_strategy(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"retry_strategy": "exponential", "status": "success"},
            {"retry_strategy": "exponential", "status": "success"},
            {"retry_strategy": "fixed", "status": "rejected"},
        ]
        result = await recommendations.best_retry_strategy(history)
        assert result["recommended_value"] == "exponential"

    async def test_recommend_with_context(self, recommendations: RecommendationEngine) -> None:
        history = [
            {"resume_id": "r1", "status": "success"},
            {"provider": "p1", "status": "success"},
        ]
        result = await recommendations.recommend(
            {
                "history": history,
                "want_resume": True,
                "want_provider": True,
            }
        )
        assert "best_resume" in result
        assert "best_provider" in result


# ── Learning Tests ──


class TestLearning:
    async def test_record_successful_application(self, learning: LearningEngine) -> None:
        await learning.record_successful_application({"job_id": "job_1"})
        assert len(learning.events) == 1
        assert learning.events[0]["data"]["outcome"] == "success"

    async def test_record_failed_application(self, learning: LearningEngine) -> None:
        await learning.record_failed_application({"job_id": "job_2"})
        assert len(learning.events) == 1
        assert learning.events[0]["data"]["outcome"] == "failure"

    async def test_record_manual_intervention(self, learning: LearningEngine) -> None:
        await learning.record_manual_intervention({"action": "edited_resume"})
        assert learning.events[0]["type"] == "manual_intervention"

    async def test_record_resume_performance(self, learning: LearningEngine) -> None:
        await learning.record_resume_performance({"resume_id": "r1", "score": 0.8})
        assert learning.events[0]["type"] == "resume_performance"

    async def test_record_ai_output(self, learning: LearningEngine) -> None:
        await learning.record_ai_output({"model": "gpt-4", "quality": 0.9})
        assert learning.events[0]["type"] == "ai_output"

    async def test_record_provider_reliability(self, learning: LearningEngine) -> None:
        await learning.record_provider_reliability({"provider": "linkedin", "uptime": 0.99})
        assert learning.events[0]["type"] == "provider_reliability"

    async def test_record_matching_quality(self, learning: LearningEngine) -> None:
        await learning.record_matching_quality({"match_score": 85})
        assert learning.events[0]["type"] == "matching_quality"

    async def test_record_workflow_history(self, learning: LearningEngine) -> None:
        await learning.record_workflow_history({"workflow_id": "wf_1"})
        assert learning.events[0]["type"] == "workflow_history"

    async def test_learned_patterns(self, learning: LearningEngine) -> None:
        await learning.record_successful_application({"job_id": "job_1"})
        await learning.record_failed_application({"job_id": "job_2"})
        patterns = await learning.learned_patterns()
        assert patterns["total_events"] == 2
        assert patterns["successful_events"] == 1
        assert patterns["failed_events"] == 1

    async def test_clear(self, learning: LearningEngine) -> None:
        await learning.record_successful_application({"job_id": "job_1"})
        learning.clear()
        assert len(learning.events) == 0


# ── Optimization Tests ──


class TestOptimization:
    async def test_optimize_matching(self, optimization: OptimizationEngine) -> None:
        history = [
            {"status": "success", "industry": "tech", "company": "Acme", "skills": ["python", "aws"]},
            {"status": "success", "industry": "tech", "company": "Beta", "skills": ["python"]},
            {"status": "rejected", "industry": "finance", "company": "Gamma", "skills": ["java"]},
        ]
        result = await optimization.optimize_matching(history, {})
        assert len(result["recommendations"]) > 0
        assert any("tech" in r for r in result["recommendations"])
        assert any("python" in r for r in result["recommendations"])

    async def test_optimize_matching_no_successful(self, optimization: OptimizationEngine) -> None:
        history = [{"status": "rejected", "industry": "finance"}]
        result = await optimization.optimize_matching(history, {})
        assert result["confidence"] == 0.0

    async def test_optimize_matching_empty_raises(self, optimization: OptimizationEngine) -> None:
        with pytest.raises(OptimizationDataError):
            await optimization.optimize_matching([], {})

    async def test_optimize_prompts(self, optimization: OptimizationEngine) -> None:
        history = [
            {"prompt_template": "t1", "status": "success", "quality": 0.9, "latency": 100, "cost": 0.01, "tokens": 500},
            {"prompt_template": "t1", "status": "success", "quality": 0.8, "latency": 150, "cost": 0.02, "tokens": 600},
            {
                "prompt_template": "t2",
                "status": "rejected",
                "quality": 0.5,
                "latency": 300,
                "cost": 0.05,
                "tokens": 1000,
            },
        ]
        result = await optimization.optimize_prompts(history)
        assert len(result) == 2
        assert result[0]["template"] == "t1"
        assert result[0]["rank"] == 1

    async def test_optimize_providers(self, optimization: OptimizationEngine) -> None:
        history = [
            {"provider": "p1", "status": "success", "latency": 100, "cost": 0.01},
            {"provider": "p1", "status": "success", "latency": 200, "cost": 0.02},
            {"provider": "p2", "status": "error", "latency": 500, "cost": 0.05},
        ]
        result = await optimization.optimize_providers(history)
        assert len(result) == 2
        assert result[0]["provider"] == "p1"
        assert result[0]["recommended"] is True

    async def test_optimize_strategies(self, optimization: OptimizationEngine) -> None:
        history = [
            {"strategy": "s1", "status": "success"},
            {"strategy": "s1", "status": "success"},
            {"strategy": "s2", "status": "rejected"},
        ]
        result = await optimization.optimize_strategies(history)
        assert result["recommendations"][0] == "Use 's1' strategy"

    async def test_optimize(self, optimization: OptimizationEngine) -> None:
        history = [{"status": "success", "strategy": "s1"}, {"status": "rejected", "strategy": "s2"}]
        result = await optimization.optimize(
            {
                "history": history,
                "optimize_strategies": True,
            }
        )
        assert "strategies" in result


# ── Scoring Tests ──


class TestScoring:
    async def test_resume_quality(self, scoring: ScoringEngine) -> None:
        data = {"ats_score": 85, "keyword_match": 75, "formatting_score": 90, "completeness": 0.8}
        result = await scoring.resume_quality(data)
        assert 0 < result["score"] < 1
        assert "ats_score" in result["components"]

    async def test_application_quality(self, scoring: ScoringEngine) -> None:
        data = {"resume_quality": 0.8, "cover_letter_quality": 0.7, "match_score": 85}
        result = await scoring.application_quality(data)
        assert 0 < result["score"] < 1

    async def test_provider_quality(self, scoring: ScoringEngine) -> None:
        data = {"success_rate": 0.9, "availability": 0.95, "latency_score": 0.8, "reliability": 0.9}
        result = await scoring.provider_quality(data)
        assert 0 < result["score"] < 1

    async def test_job_quality(self, scoring: ScoringEngine) -> None:
        data = {"match_score": 80, "salary_score": 70, "company_score": 85}
        result = await scoring.job_quality(data)
        assert 0 < result["score"] < 1

    async def test_workflow_quality(self, scoring: ScoringEngine) -> None:
        data = {"automation_score": 90, "reliability": 0.85, "efficiency": 0.8, "success_rate": 0.9}
        result = await scoring.workflow_quality(data)
        assert 0 < result["score"] < 1

    async def test_weighted_score(self, scoring: ScoringEngine) -> None:
        scores = [
            {"name": "resume", "score": 0.8, "weight": 2.0},
            {"name": "cover_letter", "score": 0.6, "weight": 1.0},
        ]
        result = await scoring.weighted_score(scores)
        assert result["score"] == pytest.approx(0.7333, rel=0.01)

    async def test_weighted_score_empty(self, scoring: ScoringEngine) -> None:
        with pytest.raises(ScoringError):
            await scoring.weighted_score([])

    async def test_score_provider(self, scoring: ScoringEngine) -> None:
        data = {"availability": 0.95, "latency": 100, "cost": 0.01, "success_rate": 0.9, "error_rate": 0.05}
        result = await scoring.score_provider(data)
        assert 0 < result["score"] < 1

    async def test_score_prompt(self, scoring: ScoringEngine) -> None:
        data = {"quality": 0.8, "latency": 200, "cost": 0.02, "success_rate": 0.85, "token_usage": 1500}
        result = await scoring.score_prompt(data)
        assert 0 < result["score"] < 1

    async def test_score_unknown_model(self, scoring: ScoringEngine) -> None:
        with pytest.raises(ScoringError):
            await scoring.score("unknown_model", {})

    async def test_label_excellent(self, scoring: ScoringEngine) -> None:
        assert scoring._label(0.95) == "excellent"

    async def test_label_good(self, scoring: ScoringEngine) -> None:
        assert scoring._label(0.80) == "good"

    async def test_label_average(self, scoring: ScoringEngine) -> None:
        assert scoring._label(0.60) == "average"

    async def test_label_below_average(self, scoring: ScoringEngine) -> None:
        assert scoring._label(0.40) == "below_average"

    async def test_label_poor(self, scoring: ScoringEngine) -> None:
        assert scoring._label(0.10) == "poor"


# ── Feedback Tests ──


class TestFeedback:
    async def test_record_feedback(self, feedback: FeedbackProcessor) -> None:
        await feedback.record_feedback("good_recommendation", {"rating": 4.5})
        history = await feedback.get_feedback_history()
        assert len(history) == 1

    async def test_get_feedback_by_category(self, feedback: FeedbackProcessor) -> None:
        await feedback.record_feedback("good_recommendation", {})
        await feedback.record_feedback("bad_recommendation", {})
        good = await feedback.get_feedback_by_category("good_recommendation")
        assert len(good) == 1

    async def test_get_feedback_summary(self, feedback: FeedbackProcessor) -> None:
        await feedback.record_feedback("good_recommendation", {"rating": 4.0})
        await feedback.record_feedback("good_recommendation", {"rating": 5.0})
        await feedback.record_feedback("bad_recommendation", {"rating": 2.0})
        summary = await feedback.get_feedback_summary()
        assert summary["total"] == 3
        assert summary["average_rating"] == pytest.approx(3.67, rel=0.01)

    async def test_empty_feedback_summary(self, feedback: FeedbackProcessor) -> None:
        summary = await feedback.get_feedback_summary()
        assert summary["total"] == 0

    async def test_clear(self, feedback: FeedbackProcessor) -> None:
        await feedback.record_feedback("good_recommendation", {})
        feedback.clear()
        assert len(feedback.feedback) == 0


# ── History Tests ──


class TestHistory:
    async def test_record_and_get(self, history: IntelligenceHistory) -> None:
        await history.record("test_event", "Test description", {"key": "value"})
        entries = await history.get_history()
        assert len(entries) == 1
        assert entries[0]["event_type"] == "test_event"

    async def test_get_by_type(self, history: IntelligenceHistory) -> None:
        await history.record("type_a", "desc", {})
        await history.record("type_b", "desc", {})
        filtered = await history.get_by_type("type_a")
        assert len(filtered) == 1

    async def test_get_recent(self, history: IntelligenceHistory) -> None:
        await history.record("test", "desc", {})
        recent = await history.get_recent(minutes=60)
        assert len(recent) == 1

    async def test_get_statistics(self, history: IntelligenceHistory) -> None:
        await history.record("type_a", "desc", {})
        await history.record("type_a", "desc", {})
        await history.record("type_b", "desc", {})
        stats = await history.get_statistics()
        assert stats["total"] == 3
        assert stats["by_type"]["type_a"] == 2
        assert stats["by_type"]["type_b"] == 1

    async def test_clear(self, history: IntelligenceHistory) -> None:
        await history.record("test", "desc", {})
        await history.clear()
        entries = await history.get_history()
        assert len(entries) == 0


# ── Experiment Tests ──


class TestExperiments:
    async def test_run_experiment(self, experiments: ExperimentEngine) -> None:
        data = [
            {"variant": "a", "status": "success", "quality": 0.9, "latency": 100},
            {"variant": "a", "status": "success", "quality": 0.8, "latency": 150},
            {"variant": "b", "status": "rejected", "quality": 0.5, "latency": 300},
            {"variant": "b", "status": "success", "quality": 0.6, "latency": 200},
        ]
        result = await experiments.run("a_b_prompt", "a", "b", data)
        assert result["winner"] == "a"
        assert result["type"] == "a_b_prompt"
        assert result["sample_size"] == 4

    async def test_run_experiment_insufficient_data(self, experiments: ExperimentEngine) -> None:
        with pytest.raises(ExperimentDataError):
            await experiments.run("a_b_prompt", "a", "b", [{"variant": "a"}])

    async def test_get_results(self, experiments: ExperimentEngine) -> None:
        data = [
            {"variant": "a", "status": "success"},
            {"variant": "a", "status": "success"},
            {"variant": "b", "status": "rejected"},
            {"variant": "b", "status": "rejected"},
        ]
        result = await experiments.run("a_b_prompt", "a", "b", data)
        retrieved = await experiments.get_results(result["id"])
        assert retrieved["id"] == result["id"]

    async def test_get_results_not_found(self, experiments: ExperimentEngine) -> None:
        with pytest.raises(ExperimentDataError):
            await experiments.get_results("nonexistent")

    async def test_list_experiments(self, experiments: ExperimentEngine) -> None:
        data = [
            {"variant": "a", "status": "success"},
            {"variant": "a", "status": "success"},
            {"variant": "b", "status": "rejected"},
            {"variant": "b", "status": "rejected"},
        ]
        await experiments.run("a_b_prompt", "a", "b", data)
        await experiments.run("provider_comparison", "p1", "p2", data)
        listings = await experiments.list_experiments()
        assert len(listings) == 2


# ── Service Tests ──


class TestService:
    async def test_service_analyze(self, service: IntelligenceService) -> None:
        data = sample_applications()
        result = await service.analyze(data)
        assert result["application_success_rate"]["rate"] == 0.6

    async def test_service_recommend(self, service: IntelligenceService) -> None:
        result = await service.recommend(
            {
                "history": sample_applications(),
                "want_resume": True,
                "want_provider": True,
            }
        )
        assert "best_resume" in result
        assert "best_provider" in result

    async def test_service_learn(self, service: IntelligenceService) -> None:
        await service.learn("test_event", {"key": "value"})
        # No error means success

    async def test_service_optimize(self, service: IntelligenceService) -> None:
        result = await service.optimize(
            {
                "history": sample_applications(),
                "optimize_strategies": True,
            }
        )
        assert "strategies" in result

    async def test_service_score(self, service: IntelligenceService) -> None:
        result = await service.score("resume_quality", {"ats_score": 85, "keyword_match": 75})
        assert result["model"] == "resume_quality"

    async def test_service_feedback(self, service: IntelligenceService) -> None:
        await service.record_feedback("good_recommendation", {"rating": 5})
        history = await service.get_feedback_history()
        assert len(history) == 1

    async def test_service_history(self, service: IntelligenceService) -> None:
        await service.record_history("test", "desc", {"k": "v"})
        entries = await service.get_history()
        assert len(entries) == 1

    async def test_service_experiment(self, service: IntelligenceService) -> None:
        data = [
            {"variant": "a", "status": "success"},
            {"variant": "a", "status": "success"},
            {"variant": "b", "status": "rejected"},
            {"variant": "b", "status": "rejected"},
        ]
        result = await service.run_experiment("a_b_prompt", "a", "b", data)
        assert result["winner"] == "a"

    async def test_analyze_specific_methods(self, service: IntelligenceService) -> None:
        data = sample_applications()
        sr = await service.analyze_application_success_rate(data)
        assert sr["rate"] == 0.6
        pr = await service.analyze_provider_success_rate(data)
        assert len(pr) == 2

    async def test_recommend_specific_methods(self, service: IntelligenceService) -> None:
        history = sample_applications()
        br = await service.recommend_best_resume(history)
        assert br["recommended_value"] == "resume_1"
        bp = await service.recommend_best_provider(history)
        assert bp["recommended_value"] == "linkedin"

    async def test_score_specific_methods(self, service: IntelligenceService) -> None:
        rq = await service.score_resume_quality({"ats_score": 90, "keyword_match": 80})
        assert rq["model"] == "resume_quality"
        pq = await service.score_provider_quality({"success_rate": 0.9, "availability": 0.95})
        assert pq["model"] == "provider_quality"
        pr = await service.score_provider(
            {"availability": 0.95, "latency": 100, "cost": 0.01, "success_rate": 0.9, "error_rate": 0.05}
        )
        assert pr["model"] == "provider_score"

    async def test_weighted_score_via_service(self, service: IntelligenceService) -> None:
        scores = [
            {"name": "a", "score": 0.8, "weight": 2.0},
            {"name": "b", "score": 0.6, "weight": 1.0},
        ]
        result = await service.weighted_score(scores)
        assert result["score"] == pytest.approx(0.7333, rel=0.01)

    async def test_history_by_type(self, service: IntelligenceService) -> None:
        await service.record_history("type_a", "desc", {})
        await service.record_history("type_b", "desc", {})
        entries = await service.get_history_by_type("type_a")
        assert len(entries) == 1

    async def test_recent_history(self, service: IntelligenceService) -> None:
        await service.record_history("test", "desc", {})
        recent = await service.get_recent_history(minutes=60)
        assert len(recent) == 1

    async def test_clear_history(self, service: IntelligenceService) -> None:
        await service.record_history("test", "desc", {})
        await service.clear_history()
        entries = await service.get_history()
        assert len(entries) == 0

    async def test_list_experiments(self, service: IntelligenceService) -> None:
        data = [
            {"variant": "a", "status": "success"},
            {"variant": "a", "status": "success"},
            {"variant": "b", "status": "rejected"},
            {"variant": "b", "status": "rejected"},
        ]
        await service.run_experiment("a_b_prompt", "a", "b", data)
        experiments_list = await service.list_experiments()
        assert len(experiments_list) == 1

    async def test_service_config(self, service: IntelligenceService) -> None:
        assert service.config.enabled is True

    async def test_learning_methods_on_service(self, service: IntelligenceService) -> None:
        await service.record_successful_application({"job_id": "j1"})
        await service.record_failed_application({"job_id": "j2"})
        await service.record_manual_intervention({"action": "fix"})
        await service.record_resume_performance({"resume_id": "r1"})
        await service.record_ai_output({"model": "gpt-4"})
        await service.record_provider_reliability({"provider": "linkedin"})
        await service.record_matching_quality({"score": 85})
        await service.record_workflow_history({"wf_id": "wf1"})
        # No errors means success

    async def test_optimization_methods_on_service(self, service: IntelligenceService) -> None:
        history = sample_applications()
        match = await service.optimize_matching(history, {"industry": "tech"})
        assert "recommendations" in match
        prompts = await service.optimize_prompts(
            [
                {
                    "prompt_template": "t1",
                    "status": "success",
                    "quality": 0.8,
                    "latency": 100,
                    "cost": 0.01,
                    "tokens": 500,
                },
            ]
        )
        assert len(prompts) == 1
        providers = await service.optimize_providers(
            [
                {"provider": "p1", "status": "success", "latency": 100, "cost": 0.01},
            ]
        )
        assert len(providers) == 1
        strategies = await service.optimize_strategies(
            [
                {"strategy": "s1", "status": "success"},
            ]
        )
        assert "recommendations" in strategies


# ── Dependency Injection Tests ──


class TestDependencies:
    async def test_get_intelligence_service(self) -> None:
        reset_intelligence_service()
        svc = get_intelligence_service()
        assert svc is not None
        assert svc.config.enabled is True

    async def test_intelligence_service_cached(self) -> None:
        reset_intelligence_service()
        svc1 = get_intelligence_service()
        svc2 = get_intelligence_service()
        assert svc1 is svc2

    async def test_reset_intelligence_service(self) -> None:
        reset_intelligence_service()
        svc1 = get_intelligence_service()
        reset_intelligence_service()
        svc2 = get_intelligence_service()
        assert svc1 is not svc2
