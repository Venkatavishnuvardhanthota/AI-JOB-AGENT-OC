import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import NotFoundError
from app.models import ResumeSection, ResumeVersion
from app.repositories import (
    ResumeSectionRepository,
    ResumeVersionRepository,
)
from app.schemas.resume import ResumeImportData
from app.services.audit import AuditService
from database.models.career_profile import CareerProfile


class ResumeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resume_repo = ResumeVersionRepository(session)
        self.section_repo = ResumeSectionRepository(session)
        self.audit_service = AuditService(session)

    # ── Resume CRUD ──

    async def list_resumes(self, user_id: uuid.UUID, archived: bool | None = None) -> list[ResumeVersion]:
        return await self.resume_repo.list_by_user(user_id, archived=archived)

    async def get_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        resume = await self.resume_repo.get_with_sections(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        return resume

    async def create_resume(
        self,
        user_id: uuid.UUID,
        title: str | None,
        description: str | None = None,
        template: str | None = None,
        resume_type: str | None = None,
        change_summary: str | None = None,
        sections: list[dict] | None = None,
    ) -> ResumeVersion:
        latest_version = await self.resume_repo.latest_version(user_id)
        resume = ResumeVersion(
            user_id=user_id,
            version=latest_version + 1,
            title=title or f"Resume v{latest_version + 1}",
            description=description,
            template=template,
            resume_type=resume_type,
            change_summary=change_summary,
            is_default=latest_version == 0,
        )
        created = await self.resume_repo.create(resume)

        if sections:
            for i, section_data in enumerate(sections):
                section = ResumeSection(
                    resume_id=created.id,
                    section_type=section_data.get("section_type", "custom"),
                    title=section_data.get("title"),
                    content=section_data.get("content"),
                    sort_order=section_data.get("sort_order", i),
                    visible=section_data.get("visible", True),
                )
                await self.section_repo.create(section)

        await self.audit_service.log(
            "RESUME_CREATED",
            user_id=user_id,
            entity="resume",
            entity_id=created.id,
            outcome="success",
        )
        return await self.resume_repo.get_with_sections(created.id)

    async def update_resume(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict,
    ) -> ResumeVersion:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        for key, value in data.items():
            if value is not None and hasattr(resume, key):
                setattr(resume, key, value)
        await self.resume_repo.update(resume)
        await self.audit_service.log(
            "RESUME_UPDATED",
            user_id=user_id,
            entity="resume",
            entity_id=resume_id,
            outcome="success",
        )
        return await self.resume_repo.get_with_sections(resume_id)

    async def delete_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> None:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        await self.resume_repo.delete(resume)
        await self.audit_service.log(
            "RESUME_DELETED",
            user_id=user_id,
            entity="resume",
            entity_id=resume_id,
            outcome="success",
        )

    # ── Status Management ──

    async def archive_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        resume.status = "archived"
        resume.archived = True
        await self.resume_repo.update(resume)
        await self.audit_service.log(
            "RESUME_ARCHIVED",
            user_id=user_id,
            entity="resume",
            entity_id=resume_id,
            outcome="success",
        )
        return resume

    async def restore_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        resume.status = "active"
        resume.archived = False
        await self.resume_repo.update(resume)
        await self.audit_service.log(
            "RESUME_RESTORED",
            user_id=user_id,
            entity="resume",
            entity_id=resume_id,
            outcome="success",
        )
        return resume

    async def set_default_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        return await self.resume_repo.set_default(resume_id, user_id)

    # ── Versioning ──

    async def create_version(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        change_summary: str | None = None,
    ) -> ResumeVersion:
        resume = await self.resume_repo.get_with_sections(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        latest_version = await self.resume_repo.latest_version(user_id)
        new_resume = ResumeVersion(
            user_id=user_id,
            version=latest_version + 1,
            title=resume.title,
            description=resume.description,
            template=resume.template,
            resume_type=resume.resume_type,
            source=resume.source,
            status="draft",
            change_summary=change_summary,
            previous_version_id=resume.id,
        )
        created = await self.resume_repo.create(new_resume)
        for section in resume.sections:
            new_section = ResumeSection(
                resume_id=created.id,
                section_type=section.section_type,
                title=section.title,
                content=section.content,
                sort_order=section.sort_order,
                visible=section.visible,
            )
            await self.section_repo.create(new_section)
        await self.audit_service.log(
            "VERSION_CREATED",
            user_id=user_id,
            entity="resume",
            entity_id=created.id,
            outcome="success",
        )
        return await self.resume_repo.get_with_sections(created.id)

    # ── Sections ──

    async def add_section(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        section_data: dict,
    ) -> ResumeSection:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        section = ResumeSection(
            resume_id=resume_id,
            section_type=section_data.get("section_type", "custom"),
            title=section_data.get("title"),
            content=section_data.get("content"),
            sort_order=section_data.get("sort_order", 0),
            visible=section_data.get("visible", True),
        )
        return await self.section_repo.create(section)

    async def update_section(
        self,
        section_id: uuid.UUID,
        user_id: uuid.UUID,
        data: dict,
    ) -> ResumeSection:
        section = await self.section_repo.get_by_id(section_id)
        if not section:
            raise NotFoundError("Section not found.")
        resume = await self.resume_repo.get_by_id(section.resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Section not found.")
        for key, value in data.items():
            if value is not None and hasattr(section, key):
                setattr(section, key, value)
        await self.section_repo.update(section)
        return section

    async def delete_section(self, section_id: uuid.UUID, user_id: uuid.UUID) -> None:
        section = await self.section_repo.get_by_id(section_id)
        if not section:
            raise NotFoundError("Section not found.")
        resume = await self.resume_repo.get_by_id(section.resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Section not found.")
        await self.section_repo.delete(section)

    # ── Import / Export ──

    async def import_resume(self, user_id: uuid.UUID, data: ResumeImportData) -> ResumeVersion:
        sections_data = [s.model_dump() for s in data.sections]
        return await self.create_resume(
            user_id=user_id,
            title=data.title,
            description=data.description,
            template=data.template,
            resume_type=data.resume_type,
            change_summary=data.change_summary or "Imported resume",
            sections=sections_data,
        )

    async def export_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion:
        return await self.get_resume(resume_id, user_id)

    # ── Upload / Parse ──

    async def parse_upload(self, content: bytes, filename: str) -> dict:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        sections = []
        needs_review = []
        title = filename

        try:
            text = content.decode("utf-8", errors="replace")
        except Exception:
            text = str(content)

        if ext == "pdf":
            sections.append({
                "section_type": "summary",
                "title": "Professional Summary",
                "content": {"text": "Extracted from PDF upload. Please review and update."},
                "sort_order": 0,
            })
            needs_review.append("summary")
        elif ext == "docx":
            sections.append({
                "section_type": "summary",
                "title": "Professional Summary",
                "content": {"text": "Extracted from DOCX upload. Please review and update."},
                "sort_order": 0,
            })
            needs_review.append("summary")
        else:
            sections.append({
                "section_type": "summary",
                "title": "Professional Summary",
                "content": {"text": text[:500] if text else "Uploaded resume content."},
                "sort_order": 0,
            })

        sections.append({
            "section_type": "experience",
            "title": "Experience",
            "content": {"text": "Uploaded resume. Please review extracted content."},
            "sort_order": 1,
        })
        needs_review.append("experience")

        sections.append({
            "section_type": "education",
            "title": "Education",
            "content": {"text": "Uploaded resume. Please review extracted content."},
            "sort_order": 2,
        })
        needs_review.append("education")

        sections.append({
            "section_type": "skills",
            "title": "Skills",
            "content": {"text": "Uploaded resume. Please review extracted content."},
            "sort_order": 3,
        })
        needs_review.append("skills")

        return {
            "title": title,
            "sections": sections,
            "confidence": 50,
            "needs_review": needs_review,
        }

    # ── Generate From Profile ──

    async def generate_from_profile(
        self,
        user_id: uuid.UUID,
        title: str = "Generated Resume",
        template: str | None = None,
        section_filter: list[str] | None = None,
    ) -> ResumeVersion:
        sections_data = []
        stmt = select(CareerProfile).options(
            joinedload(CareerProfile.education),
            joinedload(CareerProfile.experience),
            joinedload(CareerProfile.projects),
            joinedload(CareerProfile.skills),
        ).where(CareerProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        profile = result.unique().scalar_one_or_none()

        want = section_filter or ["summary", "experience", "education", "skills", "projects"]

        if "summary" in want:
            headline = (profile.headline if profile else None) or ""
            bio = (profile.bio if profile else None) or ""
            text = f"{headline}\n\n{bio}" if bio else headline or "Professional with experience in the field."
            sections_data.append({
                "section_type": "summary",
                "title": "Professional Summary",
                "content": {"text": text},
                "sort_order": 0,
            })

        if "experience" in want and profile and profile.experience:
            exp_text = "\n\n".join(
                f"{e.title} at {e.company}\n{getattr(e, 'description', '') or ''}"
                for e in profile.experience
            )
            sections_data.append({
                "section_type": "experience",
                "title": "Experience",
                "content": {"text": exp_text},
                "sort_order": 1,
            })

        if "education" in want and profile and profile.education:
            edu_text = "\n\n".join(
                f"{e.degree} - {e.institution}\n{getattr(e, 'field_of_study', '') or ''}"
                for e in profile.education
            )
            sections_data.append({
                "section_type": "education",
                "title": "Education",
                "content": {"text": edu_text},
                "sort_order": 2,
            })

        if "skills" in want and profile and profile.skills:
            skill_text = ", ".join(s.name for s in profile.skills)
            sections_data.append({
                "section_type": "skills",
                "title": "Skills",
                "content": {"text": skill_text},
                "sort_order": 3,
            })

        if "projects" in want and profile and profile.projects:
            proj_text = "\n\n".join(
                f"{p.name}\n{getattr(p, 'description', '') or ''}"
                for p in profile.projects
            )
            sections_data.append({
                "section_type": "projects",
                "title": "Projects",
                "content": {"text": proj_text},
                "sort_order": 4,
            })

        return await self.create_resume(
            user_id=user_id,
            title=title,
            template=template,
            resume_type="generated",
            change_summary="Generated from career profile",
            sections=sections_data,
        )

    # ── Duplicate ──

    async def duplicate_resume(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        change_summary: str | None = None,
    ) -> ResumeVersion:
        resume = await self.resume_repo.get_with_sections(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        latest_version = await self.resume_repo.latest_version(user_id)
        new_resume = ResumeVersion(
            user_id=user_id,
            version=latest_version + 1,
            title=title,
            description=resume.description,
            template=resume.template,
            resume_type=resume.resume_type,
            source="duplicate",
            status="draft",
            change_summary=change_summary or f"Duplicated from {resume.title}",
            previous_version_id=resume.id,
        )
        created = await self.resume_repo.create(new_resume)
        for section in (resume.sections or []):
            new_section = ResumeSection(
                resume_id=created.id,
                section_type=section.section_type,
                title=section.title,
                content=section.content,
                sort_order=section.sort_order,
                visible=section.visible,
            )
            await self.section_repo.create(new_section)
        await self.audit_service.log(
            "RESUME_DUPLICATED",
            user_id=user_id,
            entity="resume",
            entity_id=created.id,
            outcome="success",
        )
        return await self.resume_repo.get_with_sections(created.id)

    # ── Optimize For Job ──

    async def optimize_for_job(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        target_role: str | None = None,
    ) -> ResumeVersion:
        resume = await self.resume_repo.get_with_sections(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        latest_version = await self.resume_repo.latest_version(user_id)
        new_resume = ResumeVersion(
            user_id=user_id,
            version=latest_version + 1,
            title=resume.title,
            description=resume.description,
            template=resume.template,
            resume_type="optimized",
            source="optimization",
            status="draft",
            change_summary=f"Optimized for job {job_id}" + (f" ({target_role})" if target_role else ""),
            previous_version_id=resume.id,
            generated_for_job_id=job_id,
        )
        created = await self.resume_repo.create(new_resume)
        for section in (resume.sections or []):
            new_section = ResumeSection(
                resume_id=created.id,
                section_type=section.section_type,
                title=section.title,
                content=section.content,
                sort_order=section.sort_order,
                visible=section.visible,
            )
            await self.section_repo.create(new_section)
        await self.audit_service.log(
            "RESUME_OPTIMIZED",
            user_id=user_id,
            entity="resume",
            entity_id=created.id,
            outcome="success",
        )
        return await self.resume_repo.get_with_sections(created.id)

    # ── Compare Versions ──

    async def compare_versions(
        self,
        left_id: uuid.UUID,
        right_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        left = await self.resume_repo.get_with_sections(left_id)
        right = await self.resume_repo.get_with_sections(right_id)
        if not left or left.user_id != user_id:
            raise NotFoundError("Left resume not found.")
        if not right or right.user_id != user_id:
            raise NotFoundError("Right resume not found.")
        changes = []
        left_sections = {s.section_type: s for s in (left.sections or [])}
        right_sections = {s.section_type: s for s in (right.sections or [])}
        for key in set(list(left_sections.keys()) + list(right_sections.keys())):
            if key not in right_sections:
                changes.append({"type": "removed", "section": key})
            elif key not in left_sections:
                changes.append({"type": "added", "section": key})
            elif left_sections[key].content != right_sections[key].content:
                changes.append({"type": "modified", "section": key})
        return {
            "left_version": left.version,
            "right_version": right.version,
            "changes": changes,
        }
