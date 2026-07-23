from __future__ import annotations

from datetime import datetime
from typing import Any

from app.automation.cache import AutomationCache
from app.automation.config import AutomationConfig
from app.automation.exceptions import JobNotFoundError
from app.automation.history import ExecutionHistory
from app.automation.jobs import JobManager
from app.automation.policies import PolicyEnforcer
from app.automation.queue import AutomationQueue
from app.automation.scheduler import AutomationScheduler
from app.automation.schemas import (
    AutomationJob,
    AutomationPolicy,
    AutomationTrigger,
    ExecutionRecord,
    ExecutionStatus,
    HistoryQuery,
    JobPriority,
    JobState,
    QueueItem,
    QueueStatistics,
)
from app.automation.triggers import TriggerEvaluator
from app.automation.validator import AutomationValidator


class AutomationService:
    def __init__(
        self,
        config: AutomationConfig | None = None,
    ) -> None:
        self._config = config or AutomationConfig()
        self._validator = AutomationValidator(strict=self._config.strict_validation)
        self._job_manager = JobManager()
        self._queue = AutomationQueue(max_size=self._config.max_queue_size)
        self._scheduler = AutomationScheduler()
        self._history = ExecutionHistory()
        self._cache = AutomationCache(self._config)
        self._policy_enforcer = PolicyEnforcer(self._config)
        self._trigger_evaluator = TriggerEvaluator()

    def create_job(
        self,
        job_id: str,
        name: str,
        target_module: str,
        target_action: str,
        description: str = "",
        enabled: bool = True,
        priority: JobPriority = JobPriority.MEDIUM,
        automation_type: Any = None,
        trigger: AutomationTrigger | None = None,
        policy: AutomationPolicy | None = None,
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AutomationJob:
        existing = self._job_manager.get(job_id)
        from app.automation.schemas import AutomationType
        atype = automation_type or AutomationType.MANUAL
        job = AutomationJob(
            id=job_id,
            name=name,
            description=description,
            enabled=enabled,
            priority=priority,
            automation_type=atype,
            trigger=trigger or AutomationTrigger(),
            policy=policy or AutomationPolicy(),
            target_module=target_module,
            target_action=target_action,
            parameters=parameters or {},
            metadata=metadata or {},
        )
        self._validator.validate_create(job, existing)
        self._validator.validate_trigger(job.trigger)
        self._validator.validate_schedule(job)
        self._job_manager.add(job)
        self._cache.set(job_id, job)
        next_run = self._scheduler.calculate_next_run(job)
        if next_run is not None:
            job.next_run_at = next_run
            self._cache.set(job_id, job)
        return job

    def update_job(self, job: AutomationJob) -> AutomationJob:
        existing = self._job_manager.get(job.id)
        self._validator.validate_update(job, existing)
        self._validator.validate_trigger(job.trigger)
        self._validator.validate_schedule(job)
        job.updated_at = datetime.utcnow()
        self._job_manager.update(job)
        self._cache.set(job.id, job)
        next_run = self._scheduler.calculate_next_run(job)
        if next_run is not None:
            job.next_run_at = next_run
            self._cache.set(job.id, job)
        return job

    def delete_job(self, job_id: str) -> bool:
        self._job_manager.remove(job_id)
        self._cache.invalidate(job_id)
        return True

    def get_job(self, job_id: str) -> AutomationJob | None:
        cached = self._cache.get(job_id)
        if cached is not None:
            return cached
        job = self._job_manager.get(job_id)
        if job is not None:
            self._cache.set(job_id, job)
        return job

    def list_jobs(
        self,
        state: JobState | None = None,
        priority: JobPriority | None = None,
    ) -> list[AutomationJob]:
        return self._job_manager.list_jobs(state, priority)

    def pause_job(self, job_id: str) -> AutomationJob:
        job = self._get_job(job_id)
        self._validator.validate_get(job)
        job.state = JobState.PAUSED
        job.updated_at = datetime.utcnow()
        self._job_manager.update(job)
        self._cache.set(job_id, job)
        return job

    def resume_job(self, job_id: str) -> AutomationJob:
        job = self._get_job(job_id)
        if job.state != JobState.PAUSED:
            return job
        job.state = JobState.ACTIVE
        job.updated_at = datetime.utcnow()
        self._job_manager.update(job)
        self._cache.set(job_id, job)
        next_run = self._scheduler.calculate_next_run(job)
        if next_run is not None:
            job.next_run_at = next_run
            self._cache.set(job_id, job)
        return job

    def cancel_job(self, job_id: str) -> AutomationJob:
        job = self._get_job(job_id)
        self._validator.validate_cancel(job)
        job.state = JobState.CANCELLED
        job.updated_at = datetime.utcnow()
        self._job_manager.update(job)
        self._cache.set(job_id, job)
        self._queue.remove(job_id)
        return job

    def trigger_now(self, job_id: str) -> ExecutionRecord:
        job = self._get_job(job_id)
        self._validator.validate_execution(job)
        if not self._policy_enforcer.check_concurrent_jobs(job.policy):
            raise JobNotFoundError(
                message=f"Cannot trigger job '{job_id}': max concurrent jobs reached."
            )
        exec_record = ExecutionRecord(
            job_id=job_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.utcnow(),
        )
        self._queue.enqueue(job)
        job.last_run_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        self._job_manager.update(job)
        self._cache.set(job_id, job)
        return exec_record

    def calculate_next_run(self, job_id: str) -> datetime | None:
        job = self._get_job(job_id)
        return self._scheduler.calculate_next_run(job)

    def record_execution(
        self,
        job_id: str,
        status: ExecutionStatus,
        error: str | None = None,
        duration_seconds: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionRecord:
        job = self._get_job(job_id)
        record = ExecutionRecord(
            job_id=job_id,
            status=status,
            started_at=job.last_run_at or datetime.utcnow(),
            completed_at=datetime.utcnow() if status in (
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
            ) else None,
            duration_seconds=duration_seconds,
            error=error,
            metadata=metadata or {},
        )
        self._history.record(record)
        if status == ExecutionStatus.COMPLETED:
            job.state = JobState.ACTIVE
            self._policy_enforcer.release_job_slot(job_id)
        elif status == ExecutionStatus.FAILED:
            job.retry_count += 1
            self._validator.validate_retry(job)
            self._policy_enforcer.release_job_slot(job_id)
        elif status == ExecutionStatus.CANCELLED:
            self._policy_enforcer.release_job_slot(job_id)
        job.updated_at = datetime.utcnow()
        next_run = self._scheduler.calculate_next_run(job)
        if next_run is not None:
            job.next_run_at = next_run
        self._job_manager.update(job)
        self._cache.set(job_id, job)
        return record

    def list_history(
        self,
        job_id: str | None = None,
        status: ExecutionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ExecutionRecord]:
        query = HistoryQuery(
            job_id=job_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return self._history.query(query)

    def get_queue(
        self,
        priority: JobPriority | None = None,
    ) -> list[QueueItem]:
        return self._queue.get_queue(priority)

    def get_queue_statistics(self) -> QueueStatistics:
        return self._queue.get_statistics()

    def pause_queue(self) -> None:
        self._queue.pause()

    def resume_queue(self) -> None:
        self._queue.resume()

    def is_queue_paused(self) -> bool:
        return self._queue.is_paused()

    def invalidate_cache(self, job_id: str) -> None:
        self._cache.invalidate(job_id)

    def clear_cache(self) -> None:
        self._cache.clear()

    def get_active_job_count(self) -> int:
        return self._policy_enforcer.get_active_job_count()

    def _get_job(self, job_id: str) -> AutomationJob:
        job = self.get_job(job_id)
        if job is None:
            raise JobNotFoundError(
                message=f"Automation job '{job_id}' not found."
            )
        return job
