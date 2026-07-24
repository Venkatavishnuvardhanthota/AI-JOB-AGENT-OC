from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.intelligence.schemas import (
    AnalyticsResult,
    ExperimentResult,
    FeedbackRecord,
    HistoryEntry,
    LearningEvent,
    OptimizationResult,
    RecommendationResult,
    ScoreResult,
)


class AnalyticsProvider(ABC):
    @abstractmethod
    async def analyze(self, data: list[dict[str, Any]]) -> AnalyticsResult: ...


class RecommendationProvider(ABC):
    @abstractmethod
    async def recommend(self, context: dict[str, Any]) -> RecommendationResult: ...


class LearningProvider(ABC):
    @abstractmethod
    async def learn(self, event: LearningEvent) -> None: ...


class OptimizationProvider(ABC):
    @abstractmethod
    async def optimize(self, context: dict[str, Any]) -> OptimizationResult: ...


class ScoringProvider(ABC):
    @abstractmethod
    async def score(self, data: dict[str, Any]) -> ScoreResult: ...


class FeedbackProvider(ABC):
    @abstractmethod
    async def record_feedback(self, feedback: FeedbackRecord) -> None: ...


class HistoryProvider(ABC):
    @abstractmethod
    async def record(self, entry: HistoryEntry) -> None: ...

    @abstractmethod
    async def get_history(self, limit: int = 100) -> list[HistoryEntry]: ...


class ExperimentProvider(ABC):
    @abstractmethod
    async def run_experiment(self, config: dict[str, Any]) -> ExperimentResult: ...
