import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.llm import LLMMessage, LLMRequest
from app.schemas.resume_optimizer import AtsOptimizeResponse
from app.services.llm.factory import get_llm_client
from app.services.resume import ResumeService

logger = logging.getLogger(__name__)


class ATSResumeGenerator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.resume_service = ResumeService(session)

    def _strip_code_fence(self, content: str) -> str:
        if "\n" in content:
            return content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return content.replace("```json", "").replace("```", "")

    async def generate_ats_optimized(
        self,
        resume_version_id,
        job_description: str,
        company_name: str | None = None,
        job_title: str | None = None,
    ) -> AtsOptimizeResponse:
        version = await self.resume_service.get_version(resume_version_id, None)
        if not version or not version.snapshot_data:
            return AtsOptimizeResponse(
                optimized_snapshot={},
                changes_summary=(
                    "Resume version not found or missing snapshot data."
                ),
            )

        snapshot = version.snapshot_data
        client = get_llm_client()
        if not client:
            return AtsOptimizeResponse(
                optimized_snapshot=snapshot,
                changes_summary="No LLM client available for ATS optimization.",
            )

        result = await self._rewrite_for_ats(
            snapshot, job_description, company_name, job_title, client,
        )

        optimized_snapshot = result.get("optimized_snapshot", snapshot)
        changes_summary = result.get(
            "changes_summary", "ATS optimization complete.",
        )
        keywords_injected = result.get("keywords_injected", [])

        before_score = self._estimate_ats_score(snapshot, job_description)
        after_score = self._estimate_ats_score(
            optimized_snapshot, job_description,
        )

        return AtsOptimizeResponse(
            optimized_snapshot=optimized_snapshot,
            changes_summary=changes_summary,
            keywords_injected=keywords_injected,
            score_improvement=max(0, after_score - before_score),
        )

    async def _rewrite_for_ats(
        self, snapshot: dict, job_description: str,
        company_name: str | None, job_title: str | None, client,
    ) -> dict:
        snapshot_json = json.dumps(snapshot, default=str)[:4000]
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content=(
                        "You are an ATS resume optimization expert. Rewrite "
                        "the resume to maximize ATS compatibility and match "
                        "the job description.\n\n"
                        "STRICT RULES:\n"
                        "1. Keep ALL factual information intact (names, "
                        "dates, company names, institutions, job titles, "
                        "locations) - do not change, add, or remove any facts\n"
                        "2. Naturally incorporate keywords from the job "
                        "description into experience descriptions, summary, "
                        "and skills\n"
                        "3. Use standard section headings (Professional "
                        "Summary, Experience, Education, Skills, Projects, "
                        "Certifications)\n"
                        "4. Use strong action verbs (led, developed, "
                        "implemented, optimized, designed, etc.)\n"
                        "5. Quantify achievements with numbers where the "
                        "original implies scale\n"
                        "6. Rewrite bullet points to be more impactful "
                        "without changing the underlying fact\n"
                        "7. Optimize Skills section - reorder and group "
                        "skills to match job requirements\n"
                        "8. Return ONLY valid JSON with keys:\n"
                        "   - optimized_snapshot: object matching the input "
                        "snapshot structure\n"
                        "   - changes_summary: string describing key "
                        "changes made\n"
                        "   - keywords_injected: list of keyword strings "
                        "that were added\n\n"
                        "IMPORTANT: Never fabricate experience, education, "
                        "certifications, or credentials."
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"Job Title: {job_title or 'N/A'}\n"
                        f"Company: {company_name or 'N/A'}\n\n"
                        f"Job Description:\n{job_description[:3000]}\n\n"
                        f"Resume Snapshot (JSON):\n{snapshot_json}"
                    ),
                ),
            ],
            temperature=0.3,
            max_tokens=6000,
        )

        try:
            response = await client.complete(request)
            content = response.content.strip()
            if content.startswith("```"):
                content = self._strip_code_fence(content)
            result = json.loads(content)
            result.setdefault("optimized_snapshot", snapshot)
            result.setdefault("changes_summary", "ATS optimization applied.")
            result.setdefault("keywords_injected", [])
            return result
        except (json.JSONDecodeError, Exception) as e:
            logger.error("ATS rewrite failed: %s", str(e))
            return {
                "optimized_snapshot": snapshot,
                "changes_summary": f"ATS optimization failed: {str(e)}",
                "keywords_injected": [],
            }

    def _estimate_ats_score(
        self, snapshot: dict, job_description: str,
    ) -> int:
        from app.services.matching.skill_extractor import TECH_SKILLS
        text = self._snapshot_to_text(snapshot).lower()
        jd_lower = job_description.lower()
        found = 0
        total = 0
        for skill in TECH_SKILLS:
            if skill in jd_lower:
                total += 1
                if skill in text:
                    found += 1
        if total == 0:
            return 50
        return round(found / total * 100)

    def _snapshot_to_text(self, snapshot: dict) -> str:
        parts = []
        profile = snapshot.get("profile", {})
        parts.append(profile.get("summary", profile.get("bio", "")))
        parts.append(profile.get("headline", ""))
        for exp in snapshot.get("experience", []):
            parts.append(exp.get("title", ""))
            parts.append(exp.get("description", ""))
            parts.append(exp.get("company", ""))
        for edu in snapshot.get("education", []):
            parts.append(edu.get("institution", ""))
            parts.append(edu.get("degree", ""))
            parts.append(edu.get("field_of_study", ""))
        for skill in snapshot.get("skills", []):
            parts.append(skill.get("name", ""))
        for proj in snapshot.get("projects", []):
            parts.append(proj.get("name", ""))
            parts.append(proj.get("description", ""))
        for cert in snapshot.get("certifications", []):
            parts.append(cert.get("name", ""))
        return " ".join(p for p in parts if p)
