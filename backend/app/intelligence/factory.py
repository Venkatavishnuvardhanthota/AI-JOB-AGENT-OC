from __future__ import annotations

import structlog

from app.intelligence.config import IntelligenceConfig
from app.intelligence.registry import IntelligenceProviderRegistry

logger = structlog.get_logger(__name__)


class IntelligenceFactory:
    def __init__(self, registry: IntelligenceProviderRegistry, config: IntelligenceConfig) -> None:
        self._registry = registry
        self._config = config

    def register_all(self) -> None:
        if self._config.analytics_enabled:
            self._register_default_analytics()

        if self._config.recommendations_enabled:
            self._register_default_recommendations()

        if self._config.learning_enabled:
            self._register_default_learning()

        if self._config.optimization_enabled:
            self._register_default_optimization()

        if self._config.scoring_weights:
            self._register_default_scoring()

        if self._config.feedback_enabled:
            self._register_default_feedback()

        if self._config.history_enabled:
            self._register_default_history()

        if self._config.experimentation_enabled:
            self._register_default_experiments()

        logger.info("Intelligence providers registered")

    def _register_default_analytics(self) -> None:
        from app.intelligence.analytics import AnalyticsEngine

        engine = AnalyticsEngine(config=self._config)
        self._registry.register_analytics("default", engine)
        logger.info("Registered default analytics provider")

    def _register_default_recommendations(self) -> None:
        from app.intelligence.recommendations import RecommendationEngine

        engine = RecommendationEngine(config=self._config)
        self._registry.register_recommendation("default", engine)
        logger.info("Registered default recommendation provider")

    def _register_default_learning(self) -> None:
        from app.intelligence.learning import LearningEngine

        engine = LearningEngine(config=self._config)
        self._registry.register_learning("default", engine)
        logger.info("Registered default learning provider")

    def _register_default_optimization(self) -> None:
        from app.intelligence.optimization import OptimizationEngine

        engine = OptimizationEngine(config=self._config)
        self._registry.register_optimization("default", engine)
        logger.info("Registered default optimization provider")

    def _register_default_scoring(self) -> None:
        from app.intelligence.scoring import ScoringEngine

        engine = ScoringEngine(config=self._config)
        self._registry.register_scoring("default", engine)
        logger.info("Registered default scoring provider")

    def _register_default_feedback(self) -> None:
        from app.intelligence.feedback import FeedbackProcessor

        processor = FeedbackProcessor(config=self._config)
        self._registry.register_feedback("default", processor)
        logger.info("Registered default feedback provider")

    def _register_default_history(self) -> None:
        from app.intelligence.history import IntelligenceHistory

        history = IntelligenceHistory(config=self._config)
        self._registry.register_history("default", history)
        logger.info("Registered default history provider")

    def _register_default_experiments(self) -> None:
        from app.intelligence.experiments import ExperimentEngine

        engine = ExperimentEngine(config=self._config)
        self._registry.register_experiment("default", engine)
        logger.info("Registered default experiment provider")
