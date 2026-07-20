import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_run import ApplicationRun
from app.models.application_schedule import ApplicationSchedule

logger = logging.getLogger(__name__)


class ScheduleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        schedule_type: str,
        cron_expression: str | None = None,
        timezone_str: str = "UTC",
        max_applications_per_day: int = 10,
        days_of_week: list[int] | None = None,
        time_of_day: str | None = None,
    ) -> ApplicationSchedule:
        schedule = ApplicationSchedule(
            user_id=user_id,
            name=name,
            status="stopped",
            schedule_type=schedule_type,
            cron_expression=cron_expression,
            timezone=timezone_str,
            max_applications_per_day=max_applications_per_day,
            days_of_week=days_of_week or [],
            time_of_day=time_of_day,
        )
        self.session.add(schedule)
        await self.session.flush()
        await self.session.refresh(schedule)
        logger.info("Created schedule %s for user %s", schedule.id, user_id)
        return schedule

    async def get(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> ApplicationSchedule | None:
        stmt = select(ApplicationSchedule).where(
            ApplicationSchedule.id == schedule_id,
            ApplicationSchedule.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[ApplicationSchedule]:
        stmt = (
            select(ApplicationSchedule)
            .where(ApplicationSchedule.user_id == user_id)
            .order_by(ApplicationSchedule.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        schedule_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs,
    ) -> ApplicationSchedule | None:
        schedule = await self.get(schedule_id, user_id)
        if not schedule:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(schedule, key):
                setattr(schedule, key, value)
        await self.session.flush()
        await self.session.refresh(schedule)
        logger.info("Updated schedule %s", schedule_id)
        return schedule

    async def delete(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        schedule = await self.get(schedule_id, user_id)
        if not schedule:
            return False
        await self.session.delete(schedule)
        await self.session.flush()
        logger.info("Deleted schedule %s", schedule_id)
        return True

    async def start(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> ApplicationSchedule | None:
        schedule = await self.get(schedule_id, user_id)
        if not schedule:
            return None
        schedule.status = "active"
        now = datetime.now(timezone.utc)
        schedule.next_run_at = self._compute_next_run(schedule, now)
        await self.session.flush()
        await self.session.refresh(schedule)
        logger.info("Started schedule %s", schedule_id)
        return schedule

    async def stop(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> ApplicationSchedule | None:
        schedule = await self.get(schedule_id, user_id)
        if not schedule:
            return None
        schedule.status = "stopped"
        schedule.next_run_at = None
        await self.session.flush()
        await self.session.refresh(schedule)
        logger.info("Stopped schedule %s", schedule_id)
        return schedule

    async def pause(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> ApplicationSchedule | None:
        schedule = await self.get(schedule_id, user_id)
        if not schedule:
            return None
        schedule.status = "paused"
        schedule.next_run_at = None
        await self.session.flush()
        await self.session.refresh(schedule)
        logger.info("Paused schedule %s", schedule_id)
        return schedule

    async def resume(self, schedule_id: uuid.UUID, user_id: uuid.UUID) -> ApplicationSchedule | None:
        schedule = await self.get(schedule_id, user_id)
        if not schedule:
            return None
        schedule.status = "active"
        now = datetime.now(timezone.utc)
        schedule.next_run_at = self._compute_next_run(schedule, now)
        await self.session.flush()
        await self.session.refresh(schedule)
        logger.info("Resumed schedule %s", schedule_id)
        return schedule

    async def get_due_schedules(self) -> list[ApplicationSchedule]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(ApplicationSchedule)
            .where(
                ApplicationSchedule.status == "active",
                ApplicationSchedule.next_run_at <= now,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_next_run(
        self, schedule: ApplicationSchedule, last_run_at: datetime,
    ) -> None:
        schedule.last_run_at = last_run_at
        schedule.next_run_at = self._compute_next_run(schedule, last_run_at)
        await self.session.flush()

    def _compute_next_run(
        self, schedule: ApplicationSchedule, from_time: datetime,
    ) -> datetime | None:
        if schedule.schedule_type == "daily" and schedule.time_of_day:
            hour, minute = map(int, schedule.time_of_day.split(":"))
            candidate = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= from_time:
                candidate = candidate + timedelta(days=1)
            return candidate
        if schedule.schedule_type == "weekly" and schedule.days_of_week and schedule.time_of_day:
            hour, minute = map(int, schedule.time_of_day.split(":"))
            candidate = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            days_set = set(schedule.days_of_week)
            for _ in range(14):
                if candidate.weekday() in days_set and candidate > from_time:
                    return candidate
                candidate = candidate + timedelta(days=1)
            return candidate
        if schedule.schedule_type == "custom" and schedule.cron_expression:
            candidate = from_time + timedelta(days=1)
            candidate = candidate.replace(hour=0, minute=0, second=0, microsecond=0)
            return candidate
        return None


class ApplicationRunService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        job_ids: list[uuid.UUID],
        total_jobs_target: int,
        schedule_id: uuid.UUID | None = None,
    ) -> ApplicationRun:
        run = ApplicationRun(
            user_id=user_id,
            schedule_id=schedule_id,
            job_ids=[str(j) for j in job_ids],
            status="pending",
            total_jobs_target=total_jobs_target,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        logger.info("Created application run %s for user %s", run.id, user_id)
        return run

    async def get(self, run_id: uuid.UUID, user_id: uuid.UUID) -> ApplicationRun | None:
        stmt = select(ApplicationRun).where(
            ApplicationRun.id == run_id,
            ApplicationRun.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ApplicationRun]:
        stmt = (
            select(ApplicationRun)
            .where(ApplicationRun.user_id == user_id)
            .order_by(ApplicationRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        run_id: uuid.UUID,
        status: str,
        submitted_count: int | None = None,
        error_message: str | None = None,
    ) -> ApplicationRun | None:
        stmt = select(ApplicationRun).where(ApplicationRun.id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        if not run:
            return None
        run.status = status
        if submitted_count is not None:
            run.applications_submitted_count = submitted_count
        if error_message is not None:
            run.error_message = error_message
        if status in ("completed", "failed", "cancelled"):
            run.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(run)
        return run
