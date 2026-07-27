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

    RESUME_HEADINGS = [
        "summary", "professional summary", "profile", "about me",
        "experience", "work experience", "employment", "professional experience",
        "education", "academic background", "academic",
        "skills", "technical skills", "core competencies", "technologies",
        "projects", "personal projects", "professional projects",
        "certifications", "certificates", "licenses",
        "languages", "language proficiency",
        "publications", "research",
        "awards", "honors", "achievements",
        "links", "social links", "profiles",
        "additional", "additional sections", "other",
    ]

    def _classify_section(self, heading: str) -> str:
        h = heading.lower().strip().rstrip(":")
        for category, keywords in {
            "summary": ["summary", "professional summary", "profile", "about me", "objective", "career objective"],
            "experience": ["experience", "work experience", "employment", "professional experience", "work history"],
            "education": ["education", "academic", "university", "college", "school", "degree", "qualification"],
            "skills": ["skills", "competencies", "technologies", "technical", "tools", "expertise"],
            "projects": ["projects", "side projects", "professional projects"],
            "certifications": ["certifications", "certificates", "licenses", "professional development"],
            "languages": ["languages", "language"],
            "publications": ["publications", "research", "papers"],
            "awards": ["awards", "honors", "achievements", "recognition"],
            "links": ["links", "profiles", "social", "github", "linkedin", "portfolio"],
        }.items():
            if any(kw in h for kw in keywords):
                return category
        return "custom"

    def _parse_pdf_text(self, content: bytes) -> list[dict]:
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception:
            return [{"section_type": "custom", "title": "Extracted Content", "content": {"text": "Could not parse PDF."}, "sort_order": 0}]

        return self._segment_text(text)

    def _parse_docx_text(self, content: bytes) -> list[dict]:
        try:
            import docx
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            paragraphs = [(p.text, p.style.name if p.style else "") for p in doc.paragraphs]
        except Exception:
            return [{"section_type": "custom", "title": "Extracted Content", "content": {"text": "Could not parse DOCX."}, "sort_order": 0}]

        sections = []
        current_type = "summary"
        current_title = "Professional Summary"
        current_lines = []

        for text, style in paragraphs:
            if not text.strip():
                continue
            is_heading = any(h in style.lower() for h in ["heading", "title", "header"]) or (
                text.strip().rstrip(":").lower() in self.RESUME_HEADINGS
                or any(h in text.strip().rstrip(":").lower() for h in self.RESUME_HEADINGS)
            )
            if is_heading:
                if current_lines:
                    sections.append({
                        "section_type": current_type,
                        "title": current_title,
                        "content": {"text": "\n".join(current_lines).strip()},
                    })
                heading_text = text.strip().rstrip(":")
                current_type = self._classify_section(heading_text)
                current_title = heading_text
                current_lines = []
            elif current_type:
                current_lines.append(text.strip())

        if current_lines:
            sections.append({
                "section_type": current_type,
                "title": current_title,
                "content": {"text": "\n".join(current_lines).strip()},
            })

        return [s for s in sections if s.get("content", {}).get("text")]

    def _segment_text(self, text: str) -> list[dict]:
        lines = text.split("\n")
        sections = []
        current_type = "summary"
        current_title = "Professional Summary"
        current_lines = []

        def is_section_heading(line: str) -> bool:
            clean = line.strip().rstrip(":").lower()
            if clean in self.RESUME_HEADINGS:
                return True
            if sum(1 for h in self.RESUME_HEADINGS if h in clean) >= 1 and len(clean) < 60:
                return True
            return False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if is_section_heading(stripped):
                if current_lines:
                    sections.append({
                        "section_type": current_type,
                        "title": current_title,
                        "content": {"text": "\n".join(current_lines).strip()},
                    })
                heading_text = stripped.rstrip(":")
                current_type = self._classify_section(heading_text)
                current_title = heading_text
                current_lines = []
            else:
                current_lines.append(stripped)

        if current_lines:
            sections.append({
                "section_type": current_type,
                "title": current_title,
                "content": {"text": "\n".join(current_lines).strip()},
            })

        return [s for s in sections if s.get("content", {}).get("text")]

    async def parse_upload(self, content: bytes, filename: str) -> dict:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        title = filename.rsplit(".", 1)[0] if "." in filename else filename

        try:
            if ext == "pdf":
                sections = self._parse_pdf_text(content)
            elif ext == "docx":
                sections = self._parse_docx_text(content)
            else:
                text = content.decode("utf-8", errors="replace")
                sections = self._segment_text(text)

            confidence = min(90, 50 + len(sections) * 10) if sections else 0

            needs_review = []
            known_types = {"summary", "experience", "education", "skills", "projects", "certifications", "languages", "publications", "awards", "links"}
            for s in sections:
                if s["section_type"] not in known_types or not s.get("content", {}).get("text"):
                    needs_review.append(s["section_type"])
                elif s["section_type"] in ("custom",) and not s.get("title"):
                    needs_review.append(s["section_type"])

            if not sections:
                sections = [{
                    "section_type": "summary",
                    "title": "Professional Summary",
                    "content": {"text": "Uploaded resume. Please review extracted content."},
                }]
                confidence = 30
                needs_review = ["summary"]

            for i, s in enumerate(sections):
                s["sort_order"] = i

            return {
                "title": title,
                "sections": sections,
                "confidence": confidence,
                "needs_review": needs_review,
            }
        except Exception:
            return {
                "title": title,
                "sections": [{
                    "section_type": "summary",
                    "title": "Professional Summary",
                    "content": {"text": "Uploaded resume. Please review and update extracted content."},
                    "sort_order": 0,
                }],
                "confidence": 20,
                "needs_review": ["summary"],
            }

    async def reorder_sections(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        order: list[dict],
    ) -> list:
        resume = await self.resume_repo.get_with_sections(resume_id)
        if not resume or resume.user_id != user_id:
            raise NotFoundError("Resume not found.")
        updated = []
        for item in order:
            section_id = item.get("section_id")
            sort_order = item.get("sort_order", 0)
            for section in (resume.sections or []):
                if str(section.id) == str(section_id):
                    section.sort_order = sort_order
                    await self.section_repo.update(section)
                    updated.append(section)
                    break
        return updated

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
