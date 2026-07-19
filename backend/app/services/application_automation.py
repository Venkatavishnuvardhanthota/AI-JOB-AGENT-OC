import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_run import ApplicationRun
from app.models.application_schedule import ApplicationSchedule
from app.services.schedule_service import ApplicationRunService, ScheduleService

logger = logging.getLogger(__name__)


class ApplicationAutomationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def manual_apply(
        self,
        user_id: uuid.UUID,
        job_ids: list[uuid.UUID],
        max_applications: int = 5,
        schedule_id: uuid.UUID | None = None,
    ) -> ApplicationRun:
        run_service = ApplicationRunService(self.session)
        run = await run_service.create(
            user_id=user_id,
            job_ids=job_ids,
            total_jobs_target=min(len(job_ids), max_applications),
            schedule_id=schedule_id,
        )
        run = await run_service.update_status(run.id, "running", 0)
        submitted = 0
        errors: list[str] = []
        target_count = min(len(job_ids), max_applications)
        for job_id in job_ids[:target_count]:
            try:
                logger.info("User %s: applying to job %s", user_id, job_id)
                submitted += 1
            except Exception as exc:
                msg = f"Failed to apply to {job_id}: {exc}"
                errors.append(msg)
                logger.error(msg)
        final_status = "completed" if not errors else "completed_with_errors"
        error_msg = "; ".join(errors) if errors else None
        run = await run_service.update_status(
            run.id, final_status, submitted, error_msg,
        )
        return run

    async def run_scheduled_apply(
        self, schedule: ApplicationSchedule,
    ) -> ApplicationRun:
        user_id = schedule.user_id
        now = datetime.now(timezone.utc)
        daily_count = schedule.max_applications_per_day
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        used_today = await self._count_applications_today(user_id, today_start)
        remaining = max(0, daily_count - used_today)
        if remaining <= 0:
            logger.info("User %s: daily limit %d reached", user_id, daily_count)
            return None
        run_service = ApplicationRunService(self.session)
        schedule_service = ScheduleService(self.session)
        run = await run_service.create(
            user_id=user_id,
            job_ids=[],
            total_jobs_target=remaining,
            schedule_id=schedule.id,
        )
        run = await run_service.update_status(run.id, "running", 0)
        logger.info(
            "Scheduled run %s for user %s: %d jobs target",
            run.id, user_id, remaining,
        )
        run = await run_service.update_status(run.id, "completed", 0)
        await schedule_service.update_next_run(schedule, now)
        return run

    async def check_and_run_due_schedules(self) -> list[ApplicationRun]:
        schedule_service = ScheduleService(self.session)
        due_schedules = await schedule_service.get_due_schedules()
        runs: list[ApplicationRun] = []
        for schedule in due_schedules:
            try:
                run = await self.run_scheduled_apply(schedule)
                if run is not None:
                    runs.append(run)
            except Exception as exc:
                logger.error("Failed to run schedule %s: %s", schedule.id, exc)
        return runs

    async def _count_applications_today(
        self, user_id: uuid.UUID, today_start: datetime,
    ) -> int:
        stmt = select(func.coalesce(func.sum(ApplicationRun.applications_submitted_count), 0)).where(
            ApplicationRun.user_id == user_id,
            ApplicationRun.started_at >= today_start,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_daily_stats(self, user_id: uuid.UUID) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        used = await self._count_applications_today(user_id, today_start)
        total = select(func.count(ApplicationRun.id)).where(
            ApplicationRun.user_id == user_id,
        )
        total_result = await self.session.execute(total)
        total_count = total_result.scalar() or 0
        successful = select(func.count(ApplicationRun.id)).where(
            ApplicationRun.user_id == user_id,
            ApplicationRun.status == "completed",
        )
        successful_result = await self.session.execute(successful)
        successful_count = successful_result.scalar() or 0
        return {
            "applications_today": used,
            "total_runs": total_count,
            "successful_runs": successful_count,
        }
