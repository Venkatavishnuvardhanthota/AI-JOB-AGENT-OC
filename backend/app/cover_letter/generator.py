from __future__ import annotations

from app.cover_letter.config import CoverLetterConfig
from app.cover_letter.personalizer import Personalizer
from app.cover_letter.schemas import CoverLetterSection, GeneratedCoverLetter
from app.cover_letter.templates import TemplateEngine
from app.cover_letter.validator import CoverLetterValidator


class CoverLetterGenerator:
    def __init__(
        self,
        config: CoverLetterConfig,
        template_engine: TemplateEngine,
        personalizer: Personalizer,
        validator: CoverLetterValidator,
    ) -> None:
        self._config = config
        self._template_engine = template_engine
        self._personalizer = personalizer
        self._validator = validator

    def generate(
        self,
        profile,
        job_posting,
        optimized_resume,
        match_result,
    ) -> GeneratedCoverLetter:
        style = self._config.template_style
        if job_posting:
            inferred = self._infer_style(job_posting)
            if inferred:
                style = inferred

        template = self._template_engine.get_template(style)
        data = self._personalizer.extract(profile, job_posting, match_result, optimized_resume)
        variables = self._personalizer.build_variables(data, self._config.tone, style)
        sections_order = self._template_engine.get_sections_for_length(self._config.length)

        warnings: list[str] = []
        sections: list[CoverLetterSection] = []
        full_text_parts: list[str] = []

        for section_type in sections_order:
            if section_type == "greeting":
                rendered = self._template_engine.render(
                    template.get("greeting", ""), variables,
                )
                source = ["company_name"]
            elif section_type == "opening":
                rendered = self._template_engine.render(
                    template.get("opening", ""), variables,
                )
                source = ["company_name", "job_title", "career_level", "years_experience"]
            elif section_type == "company":
                rendered = self._template_engine.render(
                    template.get("company", ""), variables,
                )
                source = ["company_name", "industry"]
            elif section_type == "experience":
                rendered = self._template_engine.render(
                    template.get("experience", ""), variables,
                )
                source = ["current_role", "strengths"]
            elif section_type == "skills":
                rendered = self._template_engine.render(
                    template.get("skills", ""), variables,
                )
                source = ["primary_skills", "matching_skills"]
            elif section_type == "projects":
                rendered = self._template_engine.render(
                    template.get("projects", ""), variables,
                )
                source = ["projects"]
            elif section_type == "closing":
                rendered = self._template_engine.render(
                    template.get("closing", ""), variables,
                )
                source = ["company_name"]
            elif section_type == "signature":
                rendered = self._template_engine.render(
                    template.get("signature", ""), variables,
                )
                source = ["user_name"]
            else:
                continue

            sections.append(CoverLetterSection(
                section_type=section_type,
                content=rendered,
                source_fields=source,
            ))
            full_text_parts.append(rendered)

        full_text = "\n\n".join(full_text_parts)
        word_count = len(full_text.split())

        section_warnings = self._validator.validate_sections(
            [s.model_dump() for s in sections],
        )
        warnings.extend(section_warnings)

        output_warnings = self._validator.validate_output(
            GeneratedCoverLetter(
                full_text=full_text,
                sections=sections,
                personalization=data,
            )
        )
        warnings.extend(output_warnings)

        return GeneratedCoverLetter(
            greeting=full_text_parts[0] if len(full_text_parts) > 0 else None,
            opening_paragraph=full_text_parts[1] if len(full_text_parts) > 1 else None,
            company_paragraph=next(
                (p for s, p in zip(sections_order, full_text_parts, strict=False) if s == "company"), None
            ),
            experience_paragraph=next(
                (p for s, p in zip(sections_order, full_text_parts, strict=False) if s == "experience"), None
            ),
            skills_paragraph=next(
                (p for s, p in zip(sections_order, full_text_parts, strict=False) if s == "skills"), None
            ),
            projects_paragraph=next(
                (p for s, p in zip(sections_order, full_text_parts, strict=False) if s == "projects"), None
            ),
            closing_paragraph=full_text_parts[-2] if len(full_text_parts) >= 2 else None,
            signature=full_text_parts[-1] if len(full_text_parts) >= 1 else None,
            full_text=full_text,
            sections=sections,
            personalization=data,
            configuration={
                "tone": self._config.tone,
                "length": self._config.length,
                "template_style": style,
            },
            word_count=word_count,
            warnings=warnings,
        )

    @staticmethod
    def _infer_style(job_posting) -> str | None:
        title = getattr(job_posting, "title", "") or ""
        title_lower = title.lower()

        if any(kw in title_lower for kw in ("backend", "back-end", "server")):
            return "backend"
        if any(kw in title_lower for kw in ("software engineer", "swe", "software developer")):
            return "software_engineer"
        return None
