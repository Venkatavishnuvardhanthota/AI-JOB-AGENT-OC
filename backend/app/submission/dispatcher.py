from __future__ import annotations

from datetime import datetime

from app.submission.retry import RetryHandler
from app.submission.schemas import StrategyType, SubmissionRecord, SubmissionState
from app.submission.strategy import StrategyFactory


class Dispatcher:
    def __init__(self, retry_handler: RetryHandler) -> None:
        self._retry = retry_handler

    def dispatch(
        self,
        record: SubmissionRecord,
        strategy_type: StrategyType | None = None,
    ) -> SubmissionRecord:
        actual_strategy = strategy_type or record.strategy

        if record.dry_run:
            record.state = SubmissionState.DISPATCHED
            record.metadata["dry_run"] = True
            record.metadata["message"] = f"Dry-run: would dispatch with '{actual_strategy.value}' strategy"
            record.updated_at = datetime.utcnow()
            return record

        try:
            strategy = StrategyFactory.create(actual_strategy)
            record.strategy = actual_strategy

            env_issues = strategy.validate_environment()
            if env_issues:
                record = self._retry.mark_non_retryable(
                    record,
                    f"Environment validation failed: {'; '.join(env_issues)}",
                )
                return record

            record.state = SubmissionState.DISPATCHED
            record.dispatched_at = datetime.utcnow()
            record.updated_at = datetime.utcnow()

            result = strategy.execute(record)
            return result

        except Exception as e:
            record = self._retry.record_attempt(
                record,
                error=f"Dispatch failed: {e!s}",
            )
            return record

    def get_available_strategies(self) -> list[StrategyType]:
        return list(StrategyType)
