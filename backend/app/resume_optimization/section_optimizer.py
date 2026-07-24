from __future__ import annotations

from app.resume_optimization.keyword_extractor import KeywordExtractor
from app.resume_optimization.schemas import (
    ChangeLogEntry,
    ChangeType,
    KeywordAnalysis,
    OptimizedSection,
)


class SectionOptimizer:
    def __init__(self, keyword_extractor: KeywordExtractor) -> None:
        self._keyword_extractor = keyword_extractor

    def optimize_summary(
        self,
        original_summary: str | None,
        profile_summary: str | None,
        keywords: KeywordAnalysis,
    ) -> tuple[str | None, ChangeLogEntry | None]:
        if not original_summary and not profile_summary:
            return None, None

        base = original_summary or profile_summary or ""
        all_keywords = (
            keywords.required_keywords + keywords.preferred_keywords + keywords.technical_skills + keywords.tools
        )

        missing = [k for k in all_keywords if k.lower() not in base.lower()]
        if not missing:
            return base, ChangeLogEntry(
                section="professional_summary",
                change_type=ChangeType.UNCHANGED,
            )

        optimized = base.rstrip(".")
        if missing:
            optimized += " | Skilled in: " + ", ".join(missing[:5]) + "."

        log = ChangeLogEntry(
            section="professional_summary",
            change_type=ChangeType.REWRITTEN,
            description=f"Added {len(missing)} missing keywords to summary",
            original=base,
            optimized=optimized,
        )
        return optimized, log

    def optimize_skills(
        self,
        original_skills: list[str] | None,
        keywords: KeywordAnalysis,
    ) -> tuple[list[str], ChangeLogEntry | None]:
        if not original_skills:
            return [], None

        all_required = set(k.lower() for k in keywords.required_keywords)
        all_tech = set(k.lower() for k in keywords.technical_skills)
        all_tools = set(k.lower() for k in keywords.tools)
        all_preferred = set(k.lower() for k in keywords.preferred_keywords)

        scored: list[tuple[str, int]] = []
        for skill in original_skills:
            score = 0
            lower = skill.lower().strip()
            if lower in all_required:
                score += 3
            if lower in all_tech:
                score += 2
            if lower in all_tools:
                score += 1
            if lower in all_preferred:
                score += 2
            scored.append((skill, score))

        scored.sort(key=lambda x: -x[1])
        optimized = [s[0] for s in scored[:20]]

        missing_keywords = [
            k
            for k in keywords.required_keywords + keywords.preferred_keywords
            if k.lower() not in [s.lower().strip() for s in optimized]
        ]
        optimized.extend(missing_keywords[:5])

        log = ChangeLogEntry(
            section="skills",
            change_type=ChangeType.REORDERED,
            description="Skills reordered by job relevance",
            original=", ".join(original_skills[:10]),
            optimized=", ".join(optimized[:10]),
        )
        return optimized, log

    def optimize_experience_bullets(
        self,
        section: OptimizedSection,
        keywords: KeywordAnalysis,
    ) -> tuple[OptimizedSection, ChangeLogEntry | None]:
        original = section.original_content or ""
        if not original:
            return section, None

        all_keywords = set(
            k.lower()
            for k in (
                keywords.required_keywords + keywords.preferred_keywords + keywords.technical_skills + keywords.tools
            )
        )

        bullets = [b.strip() for b in original.split("\n") if b.strip()]
        optimized_bullets: list[str] = []
        keywords_added: set[str] = set()

        for bullet in bullets:
            lower = bullet.lower()
            missing = [k for k in all_keywords if k not in lower and k not in [ka.lower() for ka in keywords_added]]
            if missing and len(optimized_bullets) < 5:
                kw_to_add = missing[:2]
                for kw in kw_to_add:
                    bullet = bullet.rstrip(".") + f" (using {kw})"
                    keywords_added.add(kw)
            optimized_bullets.append(bullet)

        optimized = "\n".join(optimized_bullets[:5])

        log = ChangeLogEntry(
            section=f"experience:{section.title or 'unknown'}",
            change_type=ChangeType.REWRITTEN,
            description=f"Enhanced {len(keywords_added)} keywords in experience bullets",
            original=original,
            optimized=optimized,
        )

        result = OptimizedSection(
            section_type=section.section_type,
            title=section.title,
            original_content=section.original_content,
            optimized_content=optimized,
            change_type=ChangeType.REWRITTEN if keywords_added else ChangeType.UNCHANGED,
            keywords_added=list(keywords_added),
        )
        return result, log

    def optimize_projects(
        self,
        sections: list[OptimizedSection],
        keywords: KeywordAnalysis,
    ) -> tuple[list[OptimizedSection], list[ChangeLogEntry]]:
        if not sections:
            return [], []

        all_keywords = set(
            k.lower()
            for k in (
                keywords.required_keywords + keywords.preferred_keywords + keywords.technical_skills + keywords.tools
            )
        )

        scored: list[tuple[int, OptimizedSection]] = []
        for sec in sections:
            content = (sec.original_content or "") + (sec.title or "")
            lower = content.lower()
            score = sum(1 for k in all_keywords if k in lower)
            scored.append((score, sec))

        scored.sort(key=lambda x: -x[0])
        ordered = [sec for _, sec in scored]

        logs: list[ChangeLogEntry] = []
        if ordered != sections:
            logs.append(
                ChangeLogEntry(
                    section="projects",
                    change_type=ChangeType.REORDERED,
                    description="Projects reordered by job relevance",
                )
            )

        result = [
            OptimizedSection(
                section_type=sec.section_type,
                title=sec.title,
                original_content=sec.original_content,
                optimized_content=sec.optimized_content or sec.original_content,
                change_type=ChangeType.REORDERED if ordered != sections else ChangeType.UNCHANGED,
            )
            for sec in ordered
        ]
        return result, logs

    def optimize_education(
        self,
        sections: list[OptimizedSection],
        keywords: KeywordAnalysis,
    ) -> tuple[list[OptimizedSection], list[ChangeLogEntry]]:
        if not sections:
            return [], []

        all_keywords = set(
            k.lower()
            for k in (
                keywords.required_keywords
                + keywords.preferred_keywords
                + keywords.technical_skills
                + keywords.industry_terms
            )
        )

        scored: list[tuple[int, OptimizedSection]] = []
        for sec in sections:
            content = (sec.original_content or "") + (sec.title or "")
            lower = content.lower()
            score = sum(1 for k in all_keywords if k in lower)
            scored.append((score, sec))

        scored.sort(key=lambda x: -x[0])
        ordered = [sec for _, sec in scored]

        logs: list[ChangeLogEntry] = []
        if ordered != sections:
            logs.append(
                ChangeLogEntry(
                    section="education",
                    change_type=ChangeType.REORDERED,
                    description="Education reordered by job relevance",
                )
            )

        result = [
            OptimizedSection(
                section_type=sec.section_type,
                title=sec.title,
                original_content=sec.original_content,
                optimized_content=sec.optimized_content or sec.original_content,
                change_type=ChangeType.REORDERED if ordered != sections else ChangeType.UNCHANGED,
            )
            for sec in ordered
        ]
        return result, logs

    def optimize_certifications(
        self,
        sections: list[OptimizedSection],
        keywords: KeywordAnalysis,
    ) -> tuple[list[OptimizedSection], list[ChangeLogEntry]]:
        if not sections:
            return [], []
        return sections, []
