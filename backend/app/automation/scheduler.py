from __future__ import annotations

from datetime import datetime, timedelta

from app.automation.schemas import AutomationJob, AutomationType, JobState, TriggerType
from app.automation.triggers import TriggerEvaluator


class AutomationScheduler:
    def __init__(self) -> None:
        self._trigger_evaluator = TriggerEvaluator()

    def calculate_next_run(self, job: AutomationJob) -> datetime | None:
        if job.state != JobState.ACTIVE or not job.enabled:
            return None
        if job.automation_type == AutomationType.MANUAL:
            return None
        return self._trigger_evaluator.calculate_next_run(job.trigger)

    def calculate_missed_runs(self, job: AutomationJob) -> list[datetime]:
        missed: list[datetime] = []
        if job.last_run_at is None:
            return missed
        now = datetime.utcnow()
        if job.automation_type not in (AutomationType.RECURRING,):
            return missed
        next_run = job.last_run_at
        max_check = 10
        checks = 0
        while checks < max_check:
            next_run = self._trigger_evaluator.calculate_next_run(job.trigger) if job.last_run_at else None
            if next_run is None:
                break
            if next_run > now:
                break
            if next_run > job.last_run_at:
                missed.append(next_run)
            checks += 1
        return missed

    def is_eligible(self, job: AutomationJob) -> bool:
        if job.state != JobState.ACTIVE:
            return False
        if not job.enabled:
            return False
        if job.automation_type == AutomationType.MANUAL:
            return False
        if job.automation_type == AutomationType.EVENT_DRIVEN:
            return False
        next_run = self.calculate_next_run(job)
        if next_run is None:
            return False
        return datetime.utcnow() >= next_run

    def get_recurring_intervals(
        self,
        job: AutomationJob,
        count: int = 5,
    ) -> list[datetime]:
        intervals: list[datetime] = []
        if job.automation_type not in (AutomationType.RECURRING, AutomationType.ONE_TIME):
            return intervals
        next_run = self._trigger_evaluator.calculate_next_run(job.trigger)
        if next_run is None:
            return intervals
        intervals.append(next_run)
        if job.automation_type == AutomationType.ONE_TIME:
            return intervals
        for _ in range(count - 1):
            if job.trigger.trigger_type == TriggerType.DAILY and job.trigger.daily_time:
                next_run = next_run + timedelta(days=1)
                intervals.append(next_run)
            elif job.trigger.trigger_type == TriggerType.WEEKLY and job.trigger.weekly_day is not None:
                next_run = next_run + timedelta(days=7)
                intervals.append(next_run)
            elif job.trigger.trigger_type == TriggerType.MONTHLY and job.trigger.monthly_day is not None:
                month = next_run.month + 1
                year = next_run.year
                if month > 12:
                    month = 1
                    year += 1
                try:
                    next_run = next_run.replace(year=year, month=month, day=min(job.trigger.monthly_day, 28))
                except ValueError:
                    break
                intervals.append(next_run)
            else:
                break
        return intervals
