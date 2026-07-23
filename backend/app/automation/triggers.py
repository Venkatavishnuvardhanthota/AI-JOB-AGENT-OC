from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from app.automation.schemas import AutomationTrigger, TriggerType


class TriggerEvaluator:
    CRON_PATTERN = re.compile(
        r"^(\*|[0-5]?\d)\s+"
        r"(\*|[01]?\d|2[0-3])\s+"
        r"(\*|[0-2]?\d|3[01])\s+"
        r"(\*|1[0-2]|[1-9])\s+"
        r"(\*|[0-6])$"
    )

    def evaluate(self, trigger: AutomationTrigger) -> bool:
        method = self._get_evaluator(trigger.trigger_type)
        return method(trigger)

    def calculate_next_run(self, trigger: AutomationTrigger) -> datetime | None:
        method = self._get_next_run_calculator(trigger.trigger_type)
        return method(trigger)

    def validate(self, trigger: AutomationTrigger) -> list[str]:
        errors: list[str] = []
        if trigger.trigger_type == TriggerType.CRON:
            if not trigger.cron_expression:
                errors.append("Cron expression is required for CRON trigger type")
            elif not self.CRON_PATTERN.match(trigger.cron_expression):
                errors.append(
                    f"Invalid cron expression: '{trigger.cron_expression}'"
                )
        elif trigger.trigger_type == TriggerType.SCHEDULED:
            if trigger.scheduled_at is None:
                errors.append("scheduled_at is required for SCHEDULED trigger type")
        elif trigger.trigger_type == TriggerType.DAILY:
            if not trigger.daily_time:
                errors.append("daily_time is required for DAILY trigger type")
        elif trigger.trigger_type == TriggerType.WEEKLY:
            if trigger.weekly_day is None:
                errors.append("weekly_day is required for WEEKLY trigger type")
            if not trigger.weekly_time:
                errors.append("weekly_time is required for WEEKLY trigger type")
        elif trigger.trigger_type == TriggerType.MONTHLY:
            if trigger.monthly_day is None:
                errors.append("monthly_day is required for MONTHLY trigger type")
            if not trigger.monthly_time:
                errors.append("monthly_time is required for MONTHLY trigger type")
        elif trigger.trigger_type in (
            TriggerType.WORKFLOW_EVENT,
            TriggerType.REVIEW_APPROVAL,
            TriggerType.SUBMISSION_COMPLETION,
        ) and not trigger.event_source:
            errors.append(
                f"event_source is required for {trigger.trigger_type.value} trigger type"
            )
        return errors

    def _get_evaluator(self, trigger_type: TriggerType) -> Any:
        return {
            TriggerType.IMMEDIATE: self._evaluate_immediate,
            TriggerType.SCHEDULED: self._evaluate_scheduled,
            TriggerType.DAILY: self._evaluate_daily,
            TriggerType.WEEKLY: self._evaluate_weekly,
            TriggerType.MONTHLY: self._evaluate_monthly,
            TriggerType.CRON: self._evaluate_cron,
            TriggerType.WORKFLOW_EVENT: self._evaluate_event,
            TriggerType.REVIEW_APPROVAL: self._evaluate_event,
            TriggerType.SUBMISSION_COMPLETION: self._evaluate_event,
            TriggerType.MANUAL: self._evaluate_manual,
        }.get(trigger_type, self._evaluate_manual)

    def _get_next_run_calculator(self, trigger_type: TriggerType) -> Any:
        return {
            TriggerType.IMMEDIATE: self._next_run_immediate,
            TriggerType.SCHEDULED: self._next_run_scheduled,
            TriggerType.DAILY: self._next_run_daily,
            TriggerType.WEEKLY: self._next_run_weekly,
            TriggerType.MONTHLY: self._next_run_monthly,
            TriggerType.CRON: self._next_run_cron,
            TriggerType.WORKFLOW_EVENT: self._next_run_event,
            TriggerType.REVIEW_APPROVAL: self._next_run_event,
            TriggerType.SUBMISSION_COMPLETION: self._next_run_event,
            TriggerType.MANUAL: self._next_run_manual,
        }.get(trigger_type, self._next_run_manual)

    @staticmethod
    def _evaluate_immediate(trigger: AutomationTrigger) -> bool:
        return True

    @staticmethod
    def _evaluate_scheduled(trigger: AutomationTrigger) -> bool:
        if trigger.scheduled_at is None:
            return False
        return datetime.utcnow() >= trigger.scheduled_at

    @staticmethod
    def _evaluate_daily(trigger: AutomationTrigger) -> bool:
        if not trigger.daily_time:
            return False
        now = datetime.utcnow()
        target = TriggerEvaluator._parse_time_today(trigger.daily_time)
        if target is None:
            return False
        return now >= target and (now - target).total_seconds() < 86400

    @staticmethod
    def _evaluate_weekly(trigger: AutomationTrigger) -> bool:
        if trigger.weekly_day is None or not trigger.weekly_time:
            return False
        now = datetime.utcnow()
        if now.weekday() != trigger.weekly_day:
            return False
        target = TriggerEvaluator._parse_time_today(trigger.weekly_time)
        if target is None:
            return False
        return now >= target and (now - target).total_seconds() < 86400

    @staticmethod
    def _evaluate_monthly(trigger: AutomationTrigger) -> bool:
        if trigger.monthly_day is None or not trigger.monthly_time:
            return False
        now = datetime.utcnow()
        if now.day != trigger.monthly_day:
            return False
        target = TriggerEvaluator._parse_time_today(trigger.monthly_time)
        if target is None:
            return False
        return now >= target and (now - target).total_seconds() < 86400

    @staticmethod
    def _evaluate_cron(trigger: AutomationTrigger) -> bool:
        return False

    @staticmethod
    def _evaluate_event(trigger: AutomationTrigger) -> bool:
        return False

    @staticmethod
    def _evaluate_manual(trigger: AutomationTrigger) -> bool:
        return False

    @staticmethod
    def _next_run_immediate(trigger: AutomationTrigger) -> datetime:
        return datetime.utcnow()

    @staticmethod
    def _next_run_scheduled(trigger: AutomationTrigger) -> datetime | None:
        return trigger.scheduled_at

    @staticmethod
    def _next_run_daily(trigger: AutomationTrigger) -> datetime | None:
        if not trigger.daily_time:
            return None
        now = datetime.utcnow()
        target = TriggerEvaluator._parse_time_today(trigger.daily_time)
        if target is None:
            return None
        if now < target:
            return target
        return target + timedelta(days=1)

    @staticmethod
    def _next_run_weekly(trigger: AutomationTrigger) -> datetime | None:
        if trigger.weekly_day is None or not trigger.weekly_time:
            return None
        now = datetime.utcnow()
        target = TriggerEvaluator._parse_time_today(trigger.weekly_time)
        if target is None:
            return None
        days_ahead = (trigger.weekly_day - now.weekday()) % 7
        if days_ahead == 0 and now >= target:
            days_ahead = 7
        next_date = now + timedelta(days=days_ahead)
        return next_date.replace(
            hour=target.hour, minute=target.minute,
            second=target.second, microsecond=target.microsecond,
        )

    @staticmethod
    def _next_run_monthly(trigger: AutomationTrigger) -> datetime | None:
        if trigger.monthly_day is None or not trigger.monthly_time:
            return None
        now = datetime.utcnow()
        parts = trigger.monthly_time.split(":")
        hour = int(parts[0]) if parts else 0
        minute = int(parts[1]) if len(parts) > 1 else 0
        try:
            candidate = now.replace(
                day=min(trigger.monthly_day, 28),
                hour=hour, minute=minute, second=0, microsecond=0,
            )
        except ValueError:
            return None
        if now < candidate:
            return candidate
        next_month = now.month + 1
        next_year = now.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        try:
            candidate = now.replace(
                year=next_year, month=next_month,
                day=min(trigger.monthly_day, 28),
                hour=hour, minute=minute, second=0, microsecond=0,
            )
        except ValueError:
            return None
        return candidate

    @staticmethod
    def _next_run_cron(trigger: AutomationTrigger) -> datetime | None:
        return None

    @staticmethod
    def _next_run_event(trigger: AutomationTrigger) -> datetime | None:
        return None

    @staticmethod
    def _next_run_manual(trigger: AutomationTrigger) -> datetime | None:
        return None

    @staticmethod
    def _parse_time_today(time_str: str) -> datetime | None:
        try:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            second = int(parts[2]) if len(parts) > 2 else 0
            now = datetime.utcnow()
            return now.replace(
                hour=hour, minute=minute, second=second, microsecond=0,
            )
        except (ValueError, IndexError):
            return None
