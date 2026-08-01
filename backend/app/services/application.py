import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Application
from app.repositories import ApplicationAnswerRepository, ApplicationRepository, AttachmentRepository, JobRepository
from app.services.audit import AuditService
from app.services.resume_strategy import ResumeStrategyService


class ApplicationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.app_repo = ApplicationRepository(session)
        self.job_repo = JobRepository(session)
        self.answer_repo = ApplicationAnswerRepository(session)
        self.attachment_repo = AttachmentRepository(session)
        self.audit_service = AuditService(session)

    async def prepare(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        resume_id: uuid.UUID | None = None,
        resume_strategy_override: str | None = None,
        generate_cover_letter: bool = True,
        generate_ai_answers: bool = True,
    ) -> dict:
        strategy_service = ResumeStrategyService(self.session)
        result = await strategy_service.prepare_application(
            user_id=user_id,
            job_id=job_id,
            strategy_override=resume_strategy_override,
            resume_id=resume_id,
            generate_cover_letter=generate_cover_letter,
        )
        return result

    async def list_applications(
        self, user_id: uuid.UUID, status: str | None = None, page: int = 1, page_size: int = 25
    ) -> dict:
        skip = (page - 1) * page_size
        apps, total = await self.app_repo.list_by_user(user_id, status=status, skip=skip, limit=page_size)
        return {
            "data": apps,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            },
        }

    async def get_application(self, application_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Application:
        app = await self.app_repo.get_by_id(application_id)
        if not app:
            raise NotFoundError("Application not found.")
        if user_id is not None and app.user_id != user_id:
            raise NotFoundError("Application not found.")
        return app

    async def submit(self, application_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Application:
        app = await self.get_application(application_id, user_id=user_id)
        from datetime import datetime, timezone

        app.status = "Submitted"
        app.submitted_at = datetime.now(timezone.utc)
        await self.app_repo.update(app)
        await ResumeStrategyService(self.session).finalize_application(app, submitted=True)
        await self.audit_service.log(
            "APPLICATION_SUBMITTED",
            entity="application",
            entity_id=application_id,
            outcome="success",
        )
        return app

    async def cancel(self, application_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Application:
        app = await self.get_application(application_id, user_id=user_id)
        app.status = "Cancelled"
        await self.app_repo.update(app)
        await ResumeStrategyService(self.session).finalize_application(app, submitted=False)
        await self.audit_service.log(
            "APPLICATION_CANCELLED",
            entity="application",
            entity_id=application_id,
            outcome="success",
        )
        return app
