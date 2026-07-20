import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.llm import LLMMessage, LLMRequest
from app.schemas.resume_optimizer import (
    AtsScoreResponse,
    KeywordMatch,
)
from app.services.llm.factory import get_llm_client
from app.services.resume import ResumeService

logger = logging.getLogger(__name__)


class ResumeOptimizer:
    COMMON_SECTIONS = [
        "summary", "experience", "education", "skills",
        "projects", "certifications", "languages",
    ]

    def __init__(self, session: AsyncSession):
        self.session = session
        self.resume_service = ResumeService(session)

    async def analyze_keywords(
        self, resume_version_id, job_description: str
    ) -> dict:
        version = await self.resume_service.get_version(resume_version_id, None)
        if not version or not version.snapshot_data:
            return {
                "job_keywords": [],
                "present_in_resume": [],
                "missing_from_resume": [],
                "coverage_percentage": 0.0,
                "suggestions": [
                    "Resume version not found or missing snapshot data.",
                ],
            }
        snapshot = version.snapshot_data
        resume_text = self._snapshot_to_text(snapshot)
        job_keywords = await self._extract_keywords_from_jd(job_description)
        present = []
        missing = []
        resume_lower = resume_text.lower()
        for kw in job_keywords:
            if kw.keyword.lower() in resume_lower:
                present.append(kw.keyword)
            else:
                missing.append(kw)
        total = len(job_keywords)
        coverage = (len(present) / total * 100) if total > 0 else 0.0
        suggestions = self._generate_suggestions(missing, snapshot)
        return {
            "job_keywords": job_keywords,
            "present_in_resume": present,
            "missing_from_resume": missing,
            "coverage_percentage": round(coverage, 1),
            "suggestions": suggestions,
        }

    async def score_resume(
        self, resume_version_id, job_description: str,
        company_name: str | None = None, job_title: str | None = None,
    ) -> AtsScoreResponse:
        version = await self.resume_service.get_version(resume_version_id, None)
        if not version or not version.snapshot_data:
            return AtsScoreResponse(
                overall_score=0,
                recommendations=[
                    "Resume version not found or missing snapshot data.",
                ],
            )
        snapshot = version.snapshot_data
        resume_text = self._snapshot_to_text(snapshot)
        job_keywords = await self._extract_keywords_from_jd(job_description)
        client = get_llm_client()
        section_scores = []
        all_matched = []
        all_missing = []
        resume_lower = resume_text.lower()

        for kw in job_keywords:
            if kw.keyword.lower() in resume_lower:
                all_matched.append(kw)
            else:
                all_missing.append(kw)

        if client:
            try:
                llm_score = await self._llm_score(
                    snapshot, job_description, company_name, job_title, client,
                )
                section_scores = llm_score.get("section_scores", [])
                overall = llm_score.get(
                    "overall_score",
                    self._calc_keyword_score(all_matched, all_missing),
                )
                format_issues = llm_score.get("format_issues", [])
                recommendations = llm_score.get("recommendations", [])
            except Exception as e:
                logger.warning(
                    "LLM scoring failed, using keyword-only scoring: %s", e,
                )
                overall = self._calc_keyword_score(all_matched, all_missing)
                format_issues = self._check_format_issues(snapshot)
                recommendations = self._generate_recommendations(
                    all_missing, snapshot,
                )
        else:
            overall = self._calc_keyword_score(all_matched, all_missing)
            format_issues = self._check_format_issues(snapshot)
            recommendations = self._generate_recommendations(
                all_missing, snapshot,
            )

        return AtsScoreResponse(
            overall_score=overall,
            section_scores=section_scores,
            matched_keywords=all_matched,
            missing_keywords=all_missing,
            format_issues=format_issues,
            recommendations=recommendations,
        )

    async def optimize(
        self, resume_version_id, job_description: str,
        company_name: str | None = None, job_title: str | None = None,
    ) -> dict:
        version = await self.resume_service.get_version(resume_version_id, None)
        if not version or not version.snapshot_data:
            return {
                "optimized_snapshot": {},
                "changes_summary": "Resume version not found.",
                "keywords_injected": [],
                "score_improvement": 0,
            }
        snapshot = version.snapshot_data
        client = get_llm_client()
        if not client:
            return {
                "optimized_snapshot": snapshot,
                "changes_summary": "No LLM client available.",
                "keywords_injected": [],
                "score_improvement": 0,
            }
        optimized = await self._llm_rewrite(
            snapshot, job_description, company_name, job_title, client,
        )
        jd_keywords = self._extract_keywords_from_jd(job_description)
        before_text = self._snapshot_to_text(snapshot)
        before_matched = [
            kw for kw in jd_keywords
            if kw.keyword.lower() in before_text.lower()
        ]
        before_missing = [
            kw for kw in jd_keywords
            if kw.keyword.lower() not in before_text.lower()
        ]
        before_score = self._calc_keyword_score(before_matched, before_missing)
        after_text = self._snapshot_to_text(
            optimized.get("optimized_snapshot", snapshot),
        )
        after_matched_count = sum(
            1 for kw in jd_keywords
            if kw.keyword.lower() in after_text.lower()
        )
        total_kw = len(jd_keywords)
        after_pct = round(after_matched_count / total_kw * 100) if total_kw else 100
        improvement = max(0, after_pct - before_score)
        return {
            "optimized_snapshot": optimized.get("optimized_snapshot", snapshot),
            "changes_summary": optimized.get(
                "changes_summary", "Optimization complete.",
            ),
            "keywords_injected": optimized.get("keywords_injected", []),
            "score_improvement": improvement,
        }

    def _calc_keyword_score(self, matched: list, missing: list) -> int:
        total = len(matched) + len(missing)
        if total == 0:
            return 100
        return round(len(matched) / total * 100)

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
        for lang in snapshot.get("languages", []):
            parts.append(lang.get("name", ""))
        return " ".join(p for p in parts if p)

    async def _extract_keywords_from_jd(
        self, job_description: str,
    ) -> list[KeywordMatch]:
        client = get_llm_client()
        if client:
            try:
                return await self._llm_extract_keywords(job_description)
            except Exception as e:
                logger.warning(
                    "LLM keyword extraction failed, using regex fallback: %s", e,
                )
        return self._regex_extract_keywords(job_description)

    def _regex_extract_keywords(self, text: str) -> list[KeywordMatch]:
        from app.services.matching.skill_extractor import TECH_SKILLS
        found = set()
        text_lower = text.lower()
        keywords = []
        for skill in TECH_SKILLS:
            count = text_lower.count(skill)
            if count > 0:
                found.add(skill)
                keywords.append(KeywordMatch(
                    keyword=skill, category="technical",
                    found=True, frequency=count,
                ))
        words = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)
        for phrase in set(words):
            if phrase.lower() not in {s.lower() for s in found} and len(phrase) > 3:
                count = text_lower.count(phrase.lower())
                keywords.append(KeywordMatch(
                    keyword=phrase, category="general",
                    found=True, frequency=count,
                ))
        return keywords

    async def _llm_extract_keywords(self, job_description: str) -> list[KeywordMatch]:
        client = get_llm_client()
        if not client:
            return self._regex_extract_keywords(job_description)
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content=(
                        "Extract important keywords from the following job "
                        "description. Categorize each as 'technical', "
                        "'soft_skill', 'qualification', or 'general'. "
                        "Return ONLY a JSON array of objects with keys: "
                        "keyword, category, importance (high/medium/low). "
                        'Example: [{"keyword": "Python", "category": '
                        '"technical", "importance": "high"}]'
                    ),
                ),
                LLMMessage(role="user", content=job_description),
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        import json
        response = await client.complete(request)
        content = response.content.strip()
        if content.startswith("```"):
            content = self._strip_code_fence(content)
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return [
                KeywordMatch(
                    keyword=item["keyword"],
                    category=item.get("category", "general"),
                    found=True,
                    importance=item.get("importance", "medium"),
                )
                for item in parsed
            ]
        return self._regex_extract_keywords(job_description)

    async def _llm_score(
        self, snapshot: dict, job_description: str,
        company_name: str | None, job_title: str | None, client,
    ) -> dict:
        snapshot_str = str(snapshot)[:3000]
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content=(
                        "You are an ATS resume scoring expert. Analyze the "
                        "resume against the job description. "
                        "Return ONLY valid JSON with keys: overall_score "
                        "(0-100), section_scores (array of {section, score, "
                        "matched_keywords, missing_keywords, suggestions}), "
                        "format_issues (array of strings), recommendations "
                        "(array of strings). "
                        "Be strict in scoring. A top score (>90) means "
                        "near-perfect match."
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"Job Title: {job_title or 'N/A'}\n"
                        f"Company: {company_name or 'N/A'}\n\n"
                        f"Job Description:\n{job_description[:2000]}\n\n"
                        f"Resume Snapshot:\n{snapshot_str}"
                    ),
                ),
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        response = await client.complete(request)
        import json
        content = response.content.strip()
        if content.startswith("```"):
            content = self._strip_code_fence(content)
        return json.loads(content)

    async def _llm_rewrite(
        self, snapshot: dict, job_description: str,
        company_name: str | None, job_title: str | None, client,
    ) -> dict:
        snapshot_str = str(snapshot)[:3000]
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content=(
                        "You are an ATS resume optimization expert. Rewrite "
                        "the resume to maximize ATS compatibility "
                        "and match the job description. IMPORTANT rules:\n"
                        "1. Keep all factual information intact (dates, "
                        "company names, institutions, job titles)\n"
                        "2. Naturally incorporate keywords from the job "
                        "description\n"
                        "3. Use standard section headings (Summary, "
                        "Experience, Education, Skills, etc.)\n"
                        "4. Use action verbs and quantify achievements "
                        "where possible\n"
                        "5. DO NOT fabricate experience, education, "
                        "or credentials\n"
                        "6. Return ONLY valid JSON with keys: "
                        "optimized_snapshot (dict matching the input "
                        "structure), changes_summary (string explaining "
                        "key changes), keywords_injected (list of strings)."
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"Job Title: {job_title or 'N/A'}\n"
                        f"Company: {company_name or 'N/A'}\n\n"
                        f"Job Description:\n{job_description[:2000]}\n\n"
                        f"Resume Snapshot:\n{snapshot_str}"
                    ),
                ),
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        response = await client.complete(request)
        import json
        content = response.content.strip()
        if content.startswith("```"):
            content = self._strip_code_fence(content)
        return json.loads(content)

    def _strip_code_fence(self, content: str) -> str:
        if "\n" in content:
            return content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return content.replace("```json", "").replace("```", "")

    def _check_format_issues(self, snapshot: dict) -> list[str]:
        issues = []
        profile = snapshot.get("profile", {})
        if not profile.get("full_name"):
            issues.append("Missing full name in profile")
        if not snapshot.get("experience"):
            issues.append("No experience entries found")
        if not snapshot.get("skills"):
            issues.append("No skills section found")
        if not profile.get("email"):
            issues.append("Missing email address")
        return issues

    def _generate_recommendations(
        self, missing_keywords: list[KeywordMatch], snapshot: dict,
    ) -> list[str]:
        recs = []
        if missing_keywords:
            tech_missing = [
                k for k in missing_keywords if k.category == "technical"
            ]
            if tech_missing:
                recs.append(
                    f"Consider adding these technical keywords: "
                    f"{', '.join(k.keyword for k in tech_missing[:5])}",
                )
            soft_missing = [
                k for k in missing_keywords if k.category == "soft_skill"
            ]
            if soft_missing:
                recs.append(
                    f"Consider highlighting these soft skills: "
                    f"{', '.join(k.keyword for k in soft_missing[:3])}",
                )
        if not snapshot.get("summary") and not snapshot.get("profile", {}).get("bio"):
            recs.append("Add a professional summary section")
        issues = self._check_format_issues(snapshot)
        recs.extend(issues)
        return recs

    def _generate_suggestions(
        self, missing_keywords: list, snapshot: dict,
    ) -> list[str]:
        suggestions = []
        if missing_keywords:
            suggestions.append(
                f"Add these missing keywords: "
                f"{', '.join(k.keyword for k in missing_keywords[:10])}",
            )
        for kw in missing_keywords:
            section = getattr(kw, 'suggested_section', None)
            if section:
                suggestions.append(
                    f"Consider adding '{kw.keyword}' "
                    f"to the {section} section",
                )
        return suggestions
