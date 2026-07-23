from __future__ import annotations

from abc import ABC, abstractmethod

from app.submission.schemas import StrategyType, SubmissionRecord, SubmissionState


class SubmissionStrategy(ABC):
    @abstractmethod
    def get_strategy_type(self) -> StrategyType:
        ...

    @abstractmethod
    def execute(self, record: SubmissionRecord) -> SubmissionRecord:
        ...

    @abstractmethod
    def validate_environment(self) -> list[str]:
        ...

    @abstractmethod
    def get_required_fields(self) -> list[str]:
        ...


class ManualSubmissionStrategy(SubmissionStrategy):
    def get_strategy_type(self) -> StrategyType:
        return StrategyType.MANUAL

    def execute(self, record: SubmissionRecord) -> SubmissionRecord:
        record.state = SubmissionState.RUNNING
        record.metadata["manual_submission_instructions"] = (
            f"Manual submission required for package '{record.package_id}'. "
            f"Open the job posting and manually submit the application."
        )
        record.state = SubmissionState.COMPLETED
        record.completed_at = __import__("datetime").datetime.utcnow()
        return record

    def validate_environment(self) -> list[str]:
        return []

    def get_required_fields(self) -> list[str]:
        return ["package_id"]


class StrategyFactory:
    _strategies: dict[StrategyType, type[SubmissionStrategy]] = {
        StrategyType.MANUAL: ManualSubmissionStrategy,
    }

    @classmethod
    def create(cls, strategy_type: StrategyType) -> SubmissionStrategy:
        strategy_cls = cls._strategies.get(strategy_type)
        if strategy_cls is None:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return strategy_cls()

    @classmethod
    def register(cls, strategy_type: StrategyType, strategy_cls: type[SubmissionStrategy]) -> None:
        cls._strategies[strategy_type] = strategy_cls
