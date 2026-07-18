import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.generated_resume import GeneratedResume
from app.models.resume_master import ResumeMaster, ResumeVersion
from app.models.resume_template import ResumeTemplate
from app.repositories.base import BaseRepository
from app.services.resume_generator import ResumeGeneratorService
from app.services.storage import FileStorageService

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.master_repo = BaseRepository(ResumeMaster, session)
        self.version_repo = BaseRepository(ResumeVersion, session)
        self.template_repo = BaseRepository(ResumeTemplate, session)
        self.generated_repo = BaseRepository(GeneratedResume, session)
        self.generator = ResumeGeneratorService()
        self.storage = FileStorageService()

    # ── Resume Master ──

    async def list_masters(self, user_id: uuid.UUID) -> list[ResumeMaster]:
        stmt = (
            select(ResumeMaster)
            .where(ResumeMaster.user_id == user_id)
            .order_by(ResumeMaster.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_master(self, master_id: uuid.UUID, user_id: uuid.UUID) -> ResumeMaster | None:
        stmt = select(ResumeMaster).where(
            ResumeMaster.id == master_id,
            ResumeMaster.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_master(
        self, user_id: uuid.UUID, name: str, title: str | None = None,
        summary: str | None = None, template_id: uuid.UUID | None = None,
    ) -> ResumeMaster:
        return await self.master_repo.create(
            user_id=user_id,
            name=name,
            title=title,
            summary=summary,
            template_id=template_id,
        )

    async def update_master(
        self, master_id: uuid.UUID, user_id: uuid.UUID, **kwargs
    ) -> ResumeMaster | None:
        master = await self.get_master(master_id, user_id)
        if not master:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(master, key, value)
        await self.session.flush()
        await self.session.refresh(master)
        return master

    async def delete_master(self, master_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        master = await self.get_master(master_id, user_id)
        if not master:
            return False
        await self.session.delete(master)
        await self.session.flush()
        return True

    # ── Resume Versions ──

    async def list_versions(self, master_id: uuid.UUID, user_id: uuid.UUID) -> list[ResumeVersion]:
        master = await self.get_master(master_id, user_id)
        if not master:
            return []
        stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.resume_master_id == master_id)
            .order_by(ResumeVersion.version_number.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_version(self, version_id: uuid.UUID, user_id: uuid.UUID) -> ResumeVersion | None:
        stmt = (
            select(ResumeVersion)
            .join(ResumeMaster)
            .where(
                ResumeVersion.id == version_id,
                ResumeMaster.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_version(
        self, master_id: uuid.UUID, user_id: uuid.UUID,
        name: str | None = None, notes: str | None = None,
        snapshot_data: dict | None = None,
    ) -> ResumeVersion | None:
        master = await self.get_master(master_id, user_id)
        if not master:
            return None
        max_ver = 0
        versions = await self.list_versions(master_id, user_id)
        if versions:
            max_ver = versions[0].version_number
        version_name = name or f"v{max_ver + 1}"
        return await self.version_repo.create(
            resume_master_id=master_id,
            version_number=max_ver + 1,
            name=version_name,
            notes=notes,
            snapshot_data=snapshot_data,
        )

    async def get_version_snapshot(self, version_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        version = await self.get_version(version_id, user_id)
        if not version:
            return None
        return version.snapshot_data

    # ── Resume Generation ──

    async def generate_resume(
        self, version_id: uuid.UUID, user_id: uuid.UUID,
        output_format: str = "pdf", template_name: str | None = None,
    ) -> GeneratedResume | None:
        version = await self.get_version(version_id, user_id)
        if not version or not version.snapshot_data:
            return None

        snapshot = version.snapshot_data
        if template_name is None:
            master = await self.get_master(version.resume_master_id, user_id)
            if master and master.template_id:
                tmpl = await self.template_repo.get(master.template_id)
                template_name = tmpl.name.lower().replace(" ", "_") if tmpl else settings.DEFAULT_RESUME_TEMPLATE
            else:
                template_name = settings.DEFAULT_RESUME_TEMPLATE

        try:
            if output_format == "docx":
                file_bytes = self.generator.generate_docx(snapshot, template_name)
                ext = ".docx"
            else:
                file_bytes = self.generator.generate_pdf(snapshot, template_name)
                ext = ".pdf"
        except Exception as e:
            logger.error("Resume generation failed: %s", str(e))
            raise

        filename = f"resume_v{version.version_number}"
        subdir = f"users/{user_id}/generated"
        file_path = await self._save_generated_file(file_bytes, subdir, filename, ext)

        return await self.generated_repo.create(
            user_id=user_id,
            resume_version_id=version_id,
            format=output_format,
            file_path=file_path,
            file_size=len(file_bytes),
        )

    async def _save_generated_file(
        self, content: bytes, subdir: str, filename: str, ext: str
    ) -> str:
        from pathlib import Path
        base_dir = Path(settings.UPLOAD_DIR)
        dest_dir = base_dir / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{filename}_{uuid.uuid4().hex[:8]}{ext}"
        with open(dest, "wb") as f:
            f.write(content)
        return str(dest)

    async def list_generated(self, user_id: uuid.UUID) -> list[GeneratedResume]:
        stmt = (
            select(GeneratedResume)
            .where(GeneratedResume.user_id == user_id)
            .order_by(GeneratedResume.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Templates ──

    async def list_templates(self, user_id: uuid.UUID) -> list[dict]:
        builtin = self.generator.get_available_templates()
        stmt = select(ResumeTemplate).where(
            (ResumeTemplate.user_id == user_id) | (ResumeTemplate.is_system.is_(True))
        )
        result = await self.session.execute(stmt)
        db_templates = result.scalars().all()
        custom = [
            {
                "id": str(t.id),
                "name": t.name,
                "description": t.description or "",
                "is_system": t.is_system,
                "layout_config": t.layout_config,
            }
            for t in db_templates
        ]
        return builtin + custom

    async def create_template(
        self, user_id: uuid.UUID | None, name: str,
        description: str | None = None, layout_config: dict | None = None,
    ) -> ResumeTemplate:
        return await self.template_repo.create(
            user_id=user_id,
            name=name,
            description=description,
            layout_config=layout_config,
        )

    # ── Snapshot Building ──

    async def build_snapshot_from_selections(
        self, user_id: uuid.UUID,
        profile_fields: list[str] | None = None,
        education_ids: list[uuid.UUID] | None = None,
        experience_ids: list[uuid.UUID] | None = None,
        skill_ids: list[uuid.UUID] | None = None,
        project_ids: list[uuid.UUID] | None = None,
        certification_ids: list[uuid.UUID] | None = None,
        language_ids: list[uuid.UUID] | None = None,
        portfolio_item_ids: list[uuid.UUID] | None = None,
    ) -> dict:
        from app.models.certification import Certification
        from app.models.education import Education
        from app.models.experience import Experience
        from app.models.language import Language
        from app.models.portfolio_item import PortfolioItem
        from app.models.project import Project
        from app.models.skill import Skill
        from app.models.user import User
        from app.models.user_profile import UserProfile

        snapshot: dict = {}

        # Profile
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        profile = result.scalar_one_or_none()
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if profile:
            profile_data = {
                "full_name": user.full_name if user else None,
                "email": user.email if user else None,
                "phone": profile.phone,
                "headline": profile.headline,
                "bio": profile.bio,
                "location": profile.location,
                "linkedin_url": profile.linkedin_url,
                "github_url": profile.github_url,
                "portfolio_url": profile.portfolio_url,
            }
            if profile_fields:
                profile_data = {k: v for k, v in profile_data.items() if k in profile_fields}
            snapshot["profile"] = profile_data

        # Education
        if education_ids:
            stmt = select(Education).where(
                Education.id.in_(education_ids),
                Education.user_id == user_id,
            )
            result = await self.session.execute(stmt)
            snapshot["education"] = [
                {
                    "institution": e.institution,
                    "degree": e.degree,
                    "field_of_study": e.field_of_study,
                    "start_date": str(e.start_date) if e.start_date else None,
                    "end_date": str(e.end_date) if e.end_date else None,
                    "gpa": e.gpa,
                }
                for e in result.scalars().all()
            ]

        # Experience
        if experience_ids:
            stmt = select(Experience).where(
                Experience.id.in_(experience_ids),
                Experience.user_id == user_id,
            )
            result = await self.session.execute(stmt)
            snapshot["experience"] = [
                {
                    "company": e.company,
                    "title": e.title,
                    "location": e.location,
                    "start_date": str(e.start_date) if e.start_date else None,
                    "end_date": str(e.end_date) if e.end_date else None,
                    "is_current": e.is_current,
                    "description": e.description,
                }
                for e in result.scalars().all()
            ]

        # Skills
        if skill_ids:
            stmt = select(Skill).where(
                Skill.id.in_(skill_ids),
                Skill.user_id == user_id,
            )
            result = await self.session.execute(stmt)
            snapshot["skills"] = [
                {"name": s.name, "category": s.category, "proficiency": s.proficiency}
                for s in result.scalars().all()
            ]

        # Projects
        if project_ids:
            stmt = select(Project).where(
                Project.id.in_(project_ids),
                Project.user_id == user_id,
            )
            result = await self.session.execute(stmt)
            snapshot["projects"] = [
                {
                    "name": p.name,
                    "description": p.description,
                    "url": p.url,
                    "github_url": p.github_url,
                }
                for p in result.scalars().all()
            ]

        # Certifications
        if certification_ids:
            stmt = select(Certification).where(
                Certification.id.in_(certification_ids),
                Certification.user_id == user_id,
            )
            result = await self.session.execute(stmt)
            snapshot["certifications"] = [
                {
                    "name": c.name,
                    "issuer": c.issuer,
                    "issue_date": str(c.issue_date) if c.issue_date else None,
                    "credential_url": c.credential_url,
                }
                for c in result.scalars().all()
            ]

        # Languages
        if language_ids:
            stmt = select(Language).where(
                Language.id.in_(language_ids),
                Language.user_id == user_id,
            )
            result = await self.session.execute(stmt)
            snapshot["languages"] = [
                {"name": lang.name, "proficiency": lang.proficiency}
                for lang in result.scalars().all()
            ]

        # Portfolio
        if portfolio_item_ids:
            stmt = select(PortfolioItem).where(
                PortfolioItem.id.in_(portfolio_item_ids),
                PortfolioItem.user_id == user_id,
            )
            result = await self.session.execute(stmt)
            snapshot["portfolio_items"] = [
                {
                    "title": p.title,
                    "description": p.description,
                    "url": p.url,
                    "technologies": p.technologies,
                }
                for p in result.scalars().all()
            ]

        return snapshot
