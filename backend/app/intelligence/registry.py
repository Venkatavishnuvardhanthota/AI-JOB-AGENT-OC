from __future__ import annotations

import threading

import structlog

from app.intelligence.interfaces import (
    AnalyticsProvider,
    ExperimentProvider,
    FeedbackProvider,
    HistoryProvider,
    LearningProvider,
    OptimizationProvider,
    RecommendationProvider,
    ScoringProvider,
)

logger = structlog.get_logger(__name__)


class IntelligenceProviderRegistry:
    def __init__(self) -> None:
        self._analytics: dict[str, AnalyticsProvider] = {}
        self._recommendations: dict[str, RecommendationProvider] = {}
        self._learning: dict[str, LearningProvider] = {}
        self._optimization: dict[str, OptimizationProvider] = {}
        self._scoring: dict[str, ScoringProvider] = {}
        self._feedback: dict[str, FeedbackProvider] = {}
        self._history: dict[str, HistoryProvider] = {}
        self._experiments: dict[str, ExperimentProvider] = {}
        self._lock = threading.Lock()

    def register_analytics(self, name: str, provider: AnalyticsProvider) -> None:
        with self._lock:
            self._analytics[name] = provider
            logger.info("Registered analytics provider", name=name)

    def register_recommendation(self, name: str, provider: RecommendationProvider) -> None:
        with self._lock:
            self._recommendations[name] = provider
            logger.info("Registered recommendation provider", name=name)

    def register_learning(self, name: str, provider: LearningProvider) -> None:
        with self._lock:
            self._learning[name] = provider
            logger.info("Registered learning provider", name=name)

    def register_optimization(self, name: str, provider: OptimizationProvider) -> None:
        with self._lock:
            self._optimization[name] = provider
            logger.info("Registered optimization provider", name=name)

    def register_scoring(self, name: str, provider: ScoringProvider) -> None:
        with self._lock:
            self._scoring[name] = provider
            logger.info("Registered scoring provider", name=name)

    def register_feedback(self, name: str, provider: FeedbackProvider) -> None:
        with self._lock:
            self._feedback[name] = provider
            logger.info("Registered feedback provider", name=name)

    def register_history(self, name: str, provider: HistoryProvider) -> None:
        with self._lock:
            self._history[name] = provider
            logger.info("Registered history provider", name=name)

    def register_experiment(self, name: str, provider: ExperimentProvider) -> None:
        with self._lock:
            self._experiments[name] = provider
            logger.info("Registered experiment provider", name=name)

    def get_analytics(self, name: str) -> AnalyticsProvider:
        with self._lock:
            return self._analytics[name]

    def get_recommendation(self, name: str) -> RecommendationProvider:
        with self._lock:
            return self._recommendations[name]

    def get_learning(self, name: str) -> LearningProvider:
        with self._lock:
            return self._learning[name]

    def get_optimization(self, name: str) -> OptimizationProvider:
        with self._lock:
            return self._optimization[name]

    def get_scoring(self, name: str) -> ScoringProvider:
        with self._lock:
            return self._scoring[name]

    def get_feedback(self, name: str) -> FeedbackProvider:
        with self._lock:
            return self._feedback[name]

    def get_history(self, name: str) -> HistoryProvider:
        with self._lock:
            return self._history[name]

    def get_experiment(self, name: str) -> ExperimentProvider:
        with self._lock:
            return self._experiments[name]

    def list_analytics(self) -> list[str]:
        with self._lock:
            return list(self._analytics.keys())

    def list_recommendations(self) -> list[str]:
        with self._lock:
            return list(self._recommendations.keys())

    def list_learning(self) -> list[str]:
        with self._lock:
            return list(self._learning.keys())

    def list_optimization(self) -> list[str]:
        with self._lock:
            return list(self._optimization.keys())

    def list_scoring(self) -> list[str]:
        with self._lock:
            return list(self._scoring.keys())

    def list_feedback(self) -> list[str]:
        with self._lock:
            return list(self._feedback.keys())

    def list_history(self) -> list[str]:
        with self._lock:
            return list(self._history.keys())

    def list_experiments(self) -> list[str]:
        with self._lock:
            return list(self._experiments.keys())

    def has_analytics(self, name: str) -> bool:
        with self._lock:
            return name in self._analytics

    def has_recommendation(self, name: str) -> bool:
        with self._lock:
            return name in self._recommendations

    def has_learning(self, name: str) -> bool:
        with self._lock:
            return name in self._learning

    def has_optimization(self, name: str) -> bool:
        with self._lock:
            return name in self._optimization

    def has_scoring(self, name: str) -> bool:
        with self._lock:
            return name in self._scoring

    def has_feedback(self, name: str) -> bool:
        with self._lock:
            return name in self._feedback

    def has_history(self, name: str) -> bool:
        with self._lock:
            return name in self._history

    def has_experiment(self, name: str) -> bool:
        with self._lock:
            return name in self._experiments

    def clear(self) -> None:
        with self._lock:
            self._analytics.clear()
            self._recommendations.clear()
            self._learning.clear()
            self._optimization.clear()
            self._scoring.clear()
            self._feedback.clear()
            self._history.clear()
            self._experiments.clear()
