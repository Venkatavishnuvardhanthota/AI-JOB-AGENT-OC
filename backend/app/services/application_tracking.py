import csv
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.application_tracking import (
    Application,
    ApplicationNote,
    ApplicationTag,
    ApplicationTagMapping,
    ApplicationTimelineEvent,
)

logger = logging.getLogger(__name__)


class ApplicationTrackingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        job_posting_id: uuid.UUID,
        job_title: str,
        company_name: str,
        job_url: str | None = None,
        location: str | None = None,
        salary_range: str | None = None,
        status: str = "saved",
        notes: str | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        run_id: uuid.UUID | None = None,
    ) -> Application:
        existing = await self.check_duplicate(user_id, job_posting_id)
        if existing:
            raise ValueError("Already applied to this job posting.")
        app = Application(
            user_id=user_id,
            job_posting_id=job_posting_id,
            run_id=run_id,
            status=status,
            job_title=job_title,
            company_name=company_name,
            job_url=job_url,
            location=location,
            salary_range=salary_range,
            applied_at=datetime.now(timezone.utc) if status != "saved" else None,
        )
        self.session.add(app)
        await self.session.flush()
        if notes:
            note = ApplicationNote(application_id=app.id, content=notes)
            self.session.add(note)
        if tag_ids:
            for tag_id in tag_ids:
                mapping = ApplicationTagMapping(application_id=app.id, tag_id=tag_id)
                self.session.add(mapping)
        self._add_timeline(app.id, "created", f"Application created with status '{status}'")
        await self.session.flush()
        await self.session.refresh(app)
        logger.info("Created application %s for user %s", app.id, user_id)
        return app

    async def check_duplicate(self, user_id: uuid.UUID, job_posting_id: uuid.UUID) -> Application | None:
        stmt = select(Application).where(
            Application.user_id == user_id,
            Application.job_posting_id == job_posting_id,
            Application.is_active == True,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, app_id: uuid.UUID, user_id: uuid.UUID) -> Application | None:
        stmt = (
            select(Application)
            .options(joinedload(Application.tag_mappings).joinedload(ApplicationTagMapping.tag))
            .options(joinedload(Application.notes))
            .options(joinedload(Application.timeline_events))
            .where(Application.id == app_id, Application.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        company_name: str | None = None,
        search: str | None = None,
        tag_ids: list[uuid.UUID] | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Application], int]:
        base_stmt = select(Application).where(Application.user_id == user_id)
        count_stmt = select(func.count(Application.id)).where(Application.user_id == user_id)
        if status:
            base_stmt = base_stmt.where(Application.status == status)
            count_stmt = count_stmt.where(Application.status == status)
        if company_name:
            base_stmt = base_stmt.where(Application.company_name.ilike(f"%{company_name}%"))
            count_stmt = count_stmt.where(Application.company_name.ilike(f"%{company_name}%"))
        if search:
            pattern = f"%{search}%"
            base_stmt = base_stmt.where(
                Application.job_title.ilike(pattern) | Application.company_name.ilike(pattern)
            )
            count_stmt = count_stmt.where(
                Application.job_title.ilike(pattern) | Application.company_name.ilike(pattern)
            )
        if date_from:
            base_stmt = base_stmt.where(Application.applied_at >= date_from)
            count_stmt = count_stmt.where(Application.applied_at >= date_from)
        if date_to:
            base_stmt = base_stmt.where(Application.applied_at <= date_to)
            count_stmt = count_stmt.where(Application.applied_at <= date_to)
        if is_active is not None:
            base_stmt = base_stmt.where(Application.is_active == is_active)
            count_stmt = count_stmt.where(Application.is_active == is_active)
        if tag_ids:
            subq = (
                select(ApplicationTagMapping.application_id)
                .where(ApplicationTagMapping.tag_id.in_(tag_ids))
                .subquery()
            )
            base_stmt = base_stmt.where(Application.id.in_(subq))
            count_stmt = count_stmt.where(Application.id.in_(subq))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0
        base_stmt = base_stmt.options(
            joinedload(Application.tag_mappings).joinedload(ApplicationTagMapping.tag)
        )
        base_stmt = base_stmt.order_by(Application.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(base_stmt)
        applications = list(result.unique().scalars().all())
        return applications, total

    async def update(
        self,
        app_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs,
    ) -> Application | None:
        app = await self.get(app_id, user_id)
        if not app:
            return None
        old_status = app.status
        for key, value in kwargs.items():
            if value is not None and hasattr(app, key):
                setattr(app, key, value)
        new_status = kwargs.get("status", old_status)
        if new_status != old_status:
            self._add_timeline(
                app.id, "status_change",
                f"Status changed from '{old_status}' to '{new_status}'",
            )
            if new_status != "saved" and app.applied_at is None:
                app.applied_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(app)
        logger.info("Updated application %s", app_id)
        return app

    async def delete(self, app_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        app = await self.get(app_id, user_id)
        if not app:
            return False
        await self.session.delete(app)
        await self.session.flush()
        logger.info("Deleted application %s", app_id)
        return True

    async def add_note(self, app_id: uuid.UUID, user_id: uuid.UUID, content: str) -> ApplicationNote | None:
        app = await self.get(app_id, user_id)
        if not app:
            return None
        note = ApplicationNote(application_id=app_id, content=content)
        self.session.add(note)
        self._add_timeline(app_id, "note_added", "Note added")
        await self.session.flush()
        await self.session.refresh(note)
        return note

    async def get_notes(self, app_id: uuid.UUID, user_id: uuid.UUID) -> list[ApplicationNote]:
        stmt = (
            select(ApplicationNote)
            .join(Application, ApplicationNote.application_id == Application.id)
            .where(Application.id == app_id, Application.user_id == user_id)
            .order_by(ApplicationNote.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_tag_to_application(
        self, app_id: uuid.UUID, user_id: uuid.UUID, tag_id: uuid.UUID,
    ) -> bool:
        app = await self.get(app_id, user_id)
        if not app:
            return False
        existing = await self.session.execute(
            select(ApplicationTagMapping).where(
                ApplicationTagMapping.application_id == app_id,
                ApplicationTagMapping.tag_id == tag_id,
            )
        )
        if existing.scalar_one_or_none():
            return True
        mapping = ApplicationTagMapping(application_id=app_id, tag_id=tag_id)
        self.session.add(mapping)
        self._add_timeline(app_id, "tag_added", "Tag added")
        await self.session.flush()
        return True

    async def remove_tag_from_application(
        self, app_id: uuid.UUID, user_id: uuid.UUID, tag_id: uuid.UUID,
    ) -> bool:
        app = await self.get(app_id, user_id)
        if not app:
            return False
        stmt = select(ApplicationTagMapping).where(
            ApplicationTagMapping.application_id == app_id,
            ApplicationTagMapping.tag_id == tag_id,
        )
        result = await self.session.execute(stmt)
        mapping = result.scalar_one_or_none()
        if not mapping:
            return False
        await self.session.delete(mapping)
        self._add_timeline(app_id, "tag_removed", "Tag removed")
        await self.session.flush()
        return True

    async def get_timeline(
        self, app_id: uuid.UUID, user_id: uuid.UUID,
    ) -> list[ApplicationTimelineEvent]:
        stmt = (
            select(ApplicationTimelineEvent)
            .join(Application, ApplicationTimelineEvent.application_id == Application.id)
            .where(Application.id == app_id, Application.user_id == user_id)
            .order_by(ApplicationTimelineEvent.occurred_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_tag(
        self, user_id: uuid.UUID, name: str, color: str | None = None,
    ) -> ApplicationTag:
        tag = ApplicationTag(user_id=user_id, name=name, color=color)
        self.session.add(tag)
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def list_tags(self, user_id: uuid.UUID) -> list[ApplicationTag]:
        stmt = (
            select(ApplicationTag)
            .where(ApplicationTag.user_id == user_id)
            .order_by(ApplicationTag.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_tag(
        self, tag_id: uuid.UUID, user_id: uuid.UUID, **kwargs,
    ) -> ApplicationTag | None:
        stmt = select(ApplicationTag).where(
            ApplicationTag.id == tag_id, ApplicationTag.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        tag = result.scalar_one_or_none()
        if not tag:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(tag, key):
                setattr(tag, key, value)
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def delete_tag(self, tag_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(ApplicationTag).where(
            ApplicationTag.id == tag_id, ApplicationTag.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        tag = result.scalar_one_or_none()
        if not tag:
            return False
        await self.session.delete(tag)
        await self.session.flush()
        return True

    def _add_timeline(self, application_id: uuid.UUID, event_type: str, description: str) -> None:
        event = ApplicationTimelineEvent(
            application_id=application_id,
            event_type=event_type,
            description=description,
            occurred_at=datetime.now(timezone.utc),
        )
        self.session.add(event)


class ApplicationAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_analytics(self, user_id: uuid.UUID) -> dict:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        total = select(func.count(Application.id)).where(Application.user_id == user_id)
        total_result = await self.session.execute(total)
        total_count = total_result.scalar() or 0
        status_q = (
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        status_result = await self.session.execute(status_q)
        status_breakdown = [{"status": row[0], "count": row[1]} for row in status_result]
        company_q = (
            select(Application.company_name, func.count(Application.id).label("cnt"))
            .where(Application.user_id == user_id)
            .group_by(Application.company_name)
            .order_by(func.count(Application.id).desc())
            .limit(10)
        )
        company_result = await self.session.execute(company_q)
        top_companies = [{"company_name": row[0], "count": row[1]} for row in company_result]
        week_q = select(func.count(Application.id)).where(
            Application.user_id == user_id, Application.applied_at >= week_start,
        )
        week_result = await self.session.execute(week_q)
        week_count = week_result.scalar() or 0
        month_q = select(func.count(Application.id)).where(
            Application.user_id == user_id, Application.applied_at >= month_start,
        )
        month_result = await self.session.execute(month_q)
        month_count = month_result.scalar() or 0
        active_q = select(func.count(Application.id)).where(
            Application.user_id == user_id, Application.is_active == True,
        )
        active_result = await self.session.execute(active_q)
        active_count = active_result.scalar() or 0
        interview_q = select(func.count(Application.id)).where(
            Application.user_id == user_id, Application.status.in_(["interview", "offer", "accepted"]),
        )
        interview_result = await self.session.execute(interview_q)
        interview_count = interview_result.scalar() or 0
        accepted_q = select(func.count(Application.id)).where(
            Application.user_id == user_id, Application.status == "accepted",
        )
        accepted_result = await self.session.execute(accepted_q)
        accepted_count = accepted_result.scalar() or 0
        interview_rate = (interview_count / total_count * 100) if total_count > 0 else 0.0
        success_rate = (accepted_count / total_count * 100) if total_count > 0 else 0.0
        return {
            "total_applications": total_count,
            "status_breakdown": status_breakdown,
            "top_companies": top_companies,
            "applications_this_week": week_count,
            "applications_this_month": month_count,
            "active_applications": active_count,
            "interview_rate": round(interview_rate, 1),
            "success_rate": round(success_rate, 1),
        }


class ApplicationExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def export_csv(self, user_id: uuid.UUID) -> str:
        stmt = (
            select(Application)
            .options(joinedload(Application.tag_mappings).joinedload(ApplicationTagMapping.tag))
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
        )
        result = await self.session.execute(stmt)
        apps = list(result.unique().scalars().all())
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Job Title", "Company", "Status", "Location", "Salary Range",
            "Job URL", "Tags", "Applied At", "Created At", "Is Active",
        ])
        for app in apps:
            tags_str = ", ".join(m.tag.name for m in app.tag_mappings) if app.tag_mappings else ""
            writer.writerow([
                str(app.id), app.job_title, app.company_name, app.status,
                app.location or "", app.salary_range or "", app.job_url or "",
                tags_str,
                app.applied_at.isoformat() if app.applied_at else "",
                app.created_at.isoformat(),
                "Yes" if app.is_active else "No",
            ])
        return output.getvalue()
