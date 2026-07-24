from __future__ import annotations

from typing import Any

import structlog

from app.intelligence.analytics import AnalyticsEngine
from app.intelligence.config import IntelligenceConfig
from app.intelligence.exceptions import (
    AnalyticsError,
    ExperimentError,
    FeedbackError,
    HistoryError,
    LearningError,
    OptimizationError,
    RecommendationError,
)
from app.intelligence.experiments import ExperimentEngine
from app.intelligence.feedback import FeedbackProcessor
from app.intelligence.history import IntelligenceHistory
from app.intelligence.learning import LearningEngine
from app.intelligence.optimization import OptimizationEngine
from app.intelligence.recommendations import RecommendationEngine
from app.intelligence.scoring import ScoringEngine

logger = structlog.get_logger(__name__)


class IntelligenceService:
    def __init__(
        self,
        config: IntelligenceConfig,
        analytics: AnalyticsEngine | None = None,
        recommendations: RecommendationEngine | None = None,
        learning: LearningEngine | None = None,
        optimization: OptimizationEngine | None = None,
        scoring: ScoringEngine | None = None,
        feedback: FeedbackProcessor | None = None,
        history: IntelligenceHistory | None = None,
        experiments: ExperimentEngine | None = None,
    ) -> None:
        self._config = config
        self._analytics = analytics or AnalyticsEngine(config)
        self._recommendations = recommendations or RecommendationEngine(config)
        self._learning = learning or LearningEngine(config)
        self._optimization = optimization or OptimizationEngine(config)
        self._scoring = scoring or ScoringEngine(config)
        self._feedback = feedback or FeedbackProcessor(config)
        self._history = history or IntelligenceHistory(config)
        self._experiments = experiments or ExperimentEngine(config)
        self._logger = logger.bind(service="intelligence")

    # ── Analytics ──

    async def analyze(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        if not self._config.analytics_enabled:
            raise AnalyticsError("Analytics is disabled")
        if len(data) < self._config.min_data_points_for_analytics:
            raise AnalyticsError(
                f"Insufficient data: need at least {self._config.min_data_points_for_analytics} data points, "
                f"got {len(data)}"
            )
        self._logger.info("Running analytics", data_points=len(data))
        return await self._analytics.analyze(data)

    async def analyze_application_success_rate(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._analytics.application_success_rate(data)

    async def analyze_provider_success_rate(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._analytics.provider_success_rate(data)

    async def analyze_resume_effectiveness(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._analytics.resume_effectiveness(data)

    async def analyze_cover_letter_effectiveness(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._analytics.cover_letter_effectiveness(data)

    async def analyze_job_source_effectiveness(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._analytics.job_source_effectiveness(data)

    async def analyze_salary_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._analytics.salary_trends(data)

    async def analyze_location_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._analytics.location_trends(data)

    async def analyze_industry_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._analytics.industry_trends(data)

    async def analyze_company_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._analytics.company_trends(data)

    async def analyze_response_time(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._analytics.response_time(data)

    async def analyze_acceptance_rate(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._analytics.acceptance_rate(data)

    async def analyze_rejection_rate(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._analytics.rejection_rate(data)

    # ── Recommendations ──

    async def recommend(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self._config.recommendations_enabled:
            raise RecommendationError("Recommendations are disabled")
        self._logger.info("Generating recommendations", context_keys=list(context.keys()))
        return await self._recommendations.recommend(context)

    async def recommend_best_resume(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_resume(history)

    async def recommend_best_cover_letter(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_cover_letter(history)

    async def recommend_best_provider(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_provider(history)

    async def recommend_best_strategy(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_strategy(history)

    async def recommend_best_timing(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_timing(history)

    async def recommend_best_ai_model(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_ai_model(history)

    async def recommend_best_prompt_template(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_prompt_template(history)

    async def recommend_best_retry_strategy(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._recommendations.best_retry_strategy(history)

    # ── Learning ──

    async def learn(self, event_type: str, data: dict[str, Any]) -> None:
        if not self._config.learning_enabled:
            raise LearningError("Learning is disabled")
        self._logger.info("Processing learning event", event_type=event_type)
        await self._learning.learn(event_type, data)

    async def record_successful_application(self, data: dict[str, Any]) -> None:
        await self._learning.record_successful_application(data)

    async def record_failed_application(self, data: dict[str, Any]) -> None:
        await self._learning.record_failed_application(data)

    async def record_manual_intervention(self, data: dict[str, Any]) -> None:
        await self._learning.record_manual_intervention(data)

    async def record_resume_performance(self, data: dict[str, Any]) -> None:
        await self._learning.record_resume_performance(data)

    async def record_ai_output(self, data: dict[str, Any]) -> None:
        await self._learning.record_ai_output(data)

    async def record_provider_reliability(self, data: dict[str, Any]) -> None:
        await self._learning.record_provider_reliability(data)

    async def record_matching_quality(self, data: dict[str, Any]) -> None:
        await self._learning.record_matching_quality(data)

    async def record_workflow_history(self, data: dict[str, Any]) -> None:
        await self._learning.record_workflow_history(data)

    # ── Optimization ──

    async def optimize(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self._config.optimization_enabled:
            raise OptimizationError("Optimization is disabled")
        self._logger.info("Running optimization", context_keys=list(context.keys()))
        return await self._optimization.optimize(context)

    async def optimize_matching(self, history: list[dict[str, Any]], preferences: dict[str, Any]) -> dict[str, Any]:
        return await self._optimization.optimize_matching(history, preferences)

    async def optimize_prompts(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._optimization.optimize_prompts(history)

    async def optimize_providers(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._optimization.optimize_providers(history)

    async def optimize_strategies(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._optimization.optimize_strategies(history)

    # ── Scoring ──

    async def score(self, model: str, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.score(model, data)

    async def score_resume_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.resume_quality(data)

    async def score_application_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.application_quality(data)

    async def score_provider_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.provider_quality(data)

    async def score_job_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.job_quality(data)

    async def score_workflow_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.workflow_quality(data)

    async def weighted_score(self, scores: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._scoring.weighted_score(scores)

    async def score_provider(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.score_provider(data)

    async def score_prompt(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._scoring.score_prompt(data)

    # ── Feedback ──

    async def record_feedback(self, category: str, data: dict[str, Any]) -> None:
        if not self._config.feedback_enabled:
            raise FeedbackError("Feedback is disabled")
        self._logger.info("Recording feedback", category=category)
        await self._feedback.record_feedback(category, data)

    async def get_feedback_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return await self._feedback.get_feedback_history(limit)

    # ── History ──

    async def record_history(self, event_type: str, description: str, data: dict[str, Any]) -> None:
        if not self._config.history_enabled:
            raise HistoryError("History tracking is disabled")
        await self._history.record(event_type, description, data)

    async def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return await self._history.get_history(limit)

    async def get_history_by_type(self, event_type: str, limit: int = 100) -> list[dict[str, Any]]:
        return await self._history.get_by_type(event_type, limit)

    async def get_recent_history(self, minutes: int = 60) -> list[dict[str, Any]]:
        return await self._history.get_recent(minutes)

    async def clear_history(self) -> None:
        await self._history.clear()

    # ── Experiments ──

    async def run_experiment(
        self, experiment_type: str, variant_a: str, variant_b: str, data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        if not self._config.experimentation_enabled:
            raise ExperimentError("Experimentation is disabled")
        self._logger.info("Running experiment", experiment_type=experiment_type)
        return await self._experiments.run(experiment_type, variant_a, variant_b, data)

    async def get_experiment_results(self, experiment_id: str) -> dict[str, Any]:
        return await self._experiments.get_results(experiment_id)

    async def list_experiments(self) -> list[dict[str, Any]]:
        return await self._experiments.list_experiments()

    # ── Config ──

    @property
    def config(self) -> IntelligenceConfig:
        return self._config
