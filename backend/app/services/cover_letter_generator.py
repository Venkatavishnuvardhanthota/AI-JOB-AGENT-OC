import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cover_letter import CoverLetter
from app.repositories.base import BaseRepository
from app.schemas.llm import LLMMessage, LLMRequest
from app.services.company_research import CompanyResearchService
from app.services.llm.factory import get_llm_client
from app.services.llm.prompts.registry import PromptRegistry

logger = logging.getLogger(__name__)


class CoverLetterGenerator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(CoverLetter, session)
        self.registry = PromptRegistry()
        self.company_research = CompanyResearchService()

    async def generate(
        self,
        user_id: uuid.UUID,
        job_title: str,
        company_name: str,
        job_description: str,
        hiring_manager_name: str | None = None,
        user_full_name: str | None = None,
        current_role: str | None = None,
        years_experience: int | None = None,
        field: str | None = None,
        key_skills: str | None = None,
        relevant_experience: str | None = None,
        reason_for_interest: str | None = None,
        resume_snapshot: dict | None = None,
        tone: str = "professional",
        length: str = "medium",
        include_company_research: bool = True,
        job_posting_id: uuid.UUID | None = None,
    ) -> CoverLetter:
        company_info = {}
        if include_company_research:
            try:
                company_info = await self.company_research.research(company_name)
            except Exception as e:
                logger.warning("Company research failed for %s: %s", company_name, e)

        if resume_snapshot and not user_full_name:
            user_full_name = resume_snapshot.get("profile", {}).get("full_name", user_full_name)
        if resume_snapshot and not current_role:
            current_role = resume_snapshot.get("profile", {}).get("headline", current_role)
        if resume_snapshot and not key_skills:
            skills = resume_snapshot.get("skills", [])
            key_skills = ", ".join(s.get("name", "") for s in skills[:10]) if skills else key_skills
        if resume_snapshot and not relevant_experience:
            experiences = resume_snapshot.get("experience", [])
            if experiences:
                exp_texts = []
                for exp in experiences[:3]:
                    title = exp.get("title", "")
                    company = exp.get("company", "")
                    desc = (exp.get("description", "") or "")[:200]
                    exp_texts.append(f"{title} at {company}: {desc}")
                relevant_experience = "\n".join(exp_texts)

        content = await self._generate_content(
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            hiring_manager_name=hiring_manager_name,
            user_full_name=user_full_name,
            current_role=current_role or "Professional",
            years_experience=years_experience or 0,
            field=field or "my field",
            key_skills=key_skills or "",
            relevant_experience=relevant_experience or "",
            reason_for_interest=reason_for_interest or "",
            company_info=company_info,
            tone=tone,
            length=length,
        )

        max_ver = await self._get_max_version(user_id)
        cover_letter = await self.repo.create(
            user_id=user_id,
            job_posting_id=job_posting_id,
            company_name=company_name,
            job_title=job_title,
            hiring_manager_name=hiring_manager_name,
            content=content,
            version=max_ver + 1,
            is_active=True,
        )
        logger.info("Cover letter generated for %s at %s (v%d)", job_title, company_name, cover_letter.version)
        return cover_letter

    async def _generate_content(
        self,
        job_title: str,
        company_name: str,
        job_description: str,
        hiring_manager_name: str | None,
        user_full_name: str | None,
        current_role: str,
        years_experience: int,
        field: str,
        key_skills: str,
        relevant_experience: str,
        reason_for_interest: str,
        company_info: dict,
        tone: str,
        length: str,
    ) -> str:
        client = get_llm_client()
        if not client:
            return self._fallback_template(
                job_title, company_name, hiring_manager_name,
                user_full_name, current_role,
            )

        length_guide = {
            "short": "2-3 paragraphs, concise and to the point",
            "medium": "3-4 paragraphs, balanced detail",
            "long": "4-5 paragraphs, comprehensive",
        }

        tone_guide = {
            "professional": "Professional and polished tone",
            "enthusiastic": "Enthusiastic and energetic tone",
            "formal": "Formal and traditional business letter tone",
            "casual": "Conversational and approachable tone",
        }

        rendered = self.registry.render("cover-letter", {
            "job_title": job_title,
            "company_name": company_name,
            "hiring_manager_name": hiring_manager_name or "Hiring Team",
            "current_role": current_role,
            "years_experience": str(years_experience),
            "field": field,
            "key_skills": key_skills or "various relevant skills",
            "relevant_experience": relevant_experience or "I have relevant experience",
            "reason_for_interest": reason_for_interest or f"I admire {company_name}'s work in the industry",
            "applicant_name": user_full_name or "Applicant",
        })

        if rendered:
            base_template = rendered.rendered
        else:
            base_template = (
                f"Dear {hiring_manager_name or 'Hiring Team'},\n\n"
                f"I am excited to apply for the {job_title} role at {company_name}. "
                f"As a {current_role} with {years_experience} years of experience in {field}, "
                f"I bring strong skills in {key_skills}.\n\n"
                f"{relevant_experience}\n\n"
                f"I am particularly drawn to {company_name} because {reason_for_interest}.\n\n"
                f"Thank you for considering my application.\n\nSincerely,\n{user_full_name or 'Applicant'}"
            )

        company_context = ""
        if company_info:
            if company_info.get("mission"):
                company_context += f"\nCompany Mission: {company_info['mission']}"
            if company_info.get("values"):
                company_context += f"\nCompany Values: {', '.join(company_info['values'][:3])}"
            if company_info.get("products_or_services"):
                company_context += f"\nProducts/Services: {', '.join(company_info['products_or_services'][:3])}"
            if company_info.get("company_culture"):
                company_context += f"\nCulture: {company_info['company_culture']}"

        system_prompt = (
            f"You are an expert cover letter writer. Write a {tone_guide.get(tone, 'professional')} "
            f"cover letter. Length: {length_guide.get(length, '3-4 paragraphs, balanced detail')}.\n\n"
            f"Rules:\n"
            f"1. Personalize the letter based on the provided information\n"
            f"2. Address specific needs from the job description\n"
            f"3. Show enthusiasm for the role and company\n"
            f"4. Highlight relevant achievements and skills\n"
            f"5. Do NOT use placeholders like {{variable}} - substitute actual values\n"
            f"6. The letter should be ready to send without any editing\n"
            f"7. Use the user's actual name and details provided\n"
            f"8. Reference specific company details if available\n"
            f"9. Return ONLY the letter text, no additional commentary"
        )

        user_prompt = (
            f"Write a personalized cover letter using this information:\n\n"
            f"Position: {job_title}\n"
            f"Company: {company_name}\n"
            f"Hiring Manager: {hiring_manager_name or 'Hiring Team'}\n"
            f"Applicant: {user_full_name or 'Applicant'}\n"
            f"Current Role: {current_role}\n"
            f"Years Experience: {years_experience}\n"
            f"Field: {field}\n"
            f"Key Skills: {key_skills}\n"
            f"Relevant Experience:\n{relevant_experience}\n"
            f"Reason for Interest:\n{reason_for_interest}\n"
            f"Company Research:\n{company_context}\n\n"
            f"Job Description:\n{job_description[:2000]}\n\n"
            f"Draft structure:\n{base_template}"
        )

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        try:
            response = await client.complete(request)
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("\n", 1)[0] if "\n" in content else content.replace("```", "").strip()  # noqa: E501
            return content
        except Exception as e:
            logger.error("Cover letter generation failed: %s", str(e))
            return self._fallback_template(
                job_title, company_name, hiring_manager_name,
                user_full_name, current_role,
            )

    def _fallback_template(
        self, job_title: str, company_name: str,
        hiring_manager_name: str | None, user_full_name: str | None,
        current_role: str,
    ) -> str:
        manager = hiring_manager_name or "Hiring Team"
        name = user_full_name or "Applicant"
        return (
            f"Dear {manager},\n\n"
            f"I am writing to express my strong interest in the {job_title} position at {company_name}. "
            f"As a dedicated {current_role or 'professional'}, I am confident that my skills and experience "
            f"make me an excellent candidate for this role.\n\n"
            f"Throughout my career, I have developed a track record of delivering results and driving "
            f"innovation. I am eager to bring my expertise to {company_name} and contribute to "
            f"your team's success.\n\n"
            f"Thank you for considering my application. I look forward to the opportunity to discuss "
            f"how I can add value to {company_name}.\n\n"
            f"Sincerely,\n{name}"
        )

    async def list_cover_letters(self, user_id: uuid.UUID) -> list[CoverLetter]:
        stmt = (
            select(CoverLetter)
            .where(CoverLetter.user_id == user_id)
            .order_by(CoverLetter.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_cover_letter(self, cover_letter_id: uuid.UUID, user_id: uuid.UUID) -> CoverLetter | None:
        stmt = select(CoverLetter).where(
            CoverLetter.id == cover_letter_id,
            CoverLetter.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_cover_letter(self, cover_letter_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        cl = await self.get_cover_letter(cover_letter_id, user_id)
        if not cl:
            return False
        await self.session.delete(cl)
        await self.session.flush()
        return True

    async def _get_max_version(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(CoverLetter)
            .where(CoverLetter.user_id == user_id)
            .order_by(CoverLetter.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        latest = result.scalar_one_or_none()
        return latest.version if latest else 0

    async def export_cover_letter(
        self, cover_letter_id: uuid.UUID, user_id: uuid.UUID,
        export_format: str = "pdf",
    ) -> CoverLetter | None:
        cl = await self.get_cover_letter(cover_letter_id, user_id)
        if not cl:
            return None

        from app.services.resume_generator import ResumeGeneratorService
        generator = ResumeGeneratorService()

        snapshot = {
            "profile": {
                "full_name": "Cover Letter",
                "email": "",
                "headline": f"Application for {cl.job_title} at {cl.company_name}",
            },
            "summary": cl.content,
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "languages": [],
            "portfolio_items": [],
        }

        try:
            if export_format == "docx":
                file_bytes = generator.generate_docx(snapshot, "modern")
                ext = ".docx"
            else:
                file_bytes = generator.generate_pdf(snapshot, "modern")
                ext = ".pdf"

            from pathlib import Path

            from app.core.config import settings
            base_dir = Path(settings.UPLOAD_DIR)
            dest_dir = base_dir / f"users/{user_id}/cover_letters"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f"cover_letter_v{cl.version}_{uuid.uuid4().hex[:8]}{ext}"
            with open(dest, "wb") as f:
                f.write(file_bytes)

            cl.file_path = str(dest)
            cl.file_format = export_format
            await self.session.flush()
            await self.session.refresh(cl)
            return cl
        except Exception as e:
            logger.error("Cover letter export failed: %s", str(e))
            return cl
