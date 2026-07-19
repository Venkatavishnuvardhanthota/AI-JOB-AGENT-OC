import logging

from app.schemas.llm import LLMMessage, LLMRequest
from app.services.llm.factory import get_llm_client

logger = logging.getLogger(__name__)


class ResumeKeywordOptimizer:
    def _strip_code_fence(self, content: str) -> str:
        if "\n" in content:
            return content.split("\n", 1)[-1].rsplit("\n", 1)[0]
        return content.replace("```json", "").replace("```", "")

    async def optimize_section(
        self, section: str, original_text: str, target_keywords: list[str],
        context: dict | None = None,
    ) -> dict:
        client = get_llm_client()
        if not client:
            return {
                "section": section,
                "original_text": original_text,
                "optimized_text": original_text,
                "keywords_added": [],
                "keywords_kept": [],
            }
        keywords_str = ", ".join(target_keywords)
        context_str = str(context)[:1000] if context else ""
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content=(
                        "You are an ATS keyword optimization expert. Rewrite "
                        "the given resume section text to naturally incorporate "
                        "the target keywords while maintaining readability and "
                        "professional tone.\n\n"
                        "Rules:\n"
                        "1. Keywords must be integrated naturally - "
                        "do not just list them\n"
                        "2. Do not change factual information "
                        "(dates, company names, institutions)\n"
                        "3. Use synonyms and related terms where appropriate\n"
                        "4. Maintain the same length and style as the original\n"
                        "5. Return ONLY valid JSON with keys: optimized_text "
                        "(string), keywords_added (list of strings), "
                        "keywords_kept (list of strings that were already "
                        "present)"
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"Section: {section}\n\n"
                        f"Original text:\n{original_text}\n\n"
                        f"Target keywords to incorporate:\n{keywords_str}\n\n"
                        f"Additional context:\n{context_str}"
                    ),
                ),
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        try:
            response = await client.complete(request)
            import json
            content = response.content.strip()
            if content.startswith("```"):
                content = self._strip_code_fence(content)
            result = json.loads(content)
            result["section"] = section
            result["original_text"] = original_text
            result.setdefault("optimized_text", original_text)
            result.setdefault("keywords_added", [])
            result.setdefault("keywords_kept", [])
            return result
        except Exception as e:
            logger.warning(
                "Keyword optimization failed for section %s: %s",
                section, str(e),
            )
            return {
                "section": section,
                "original_text": original_text,
                "optimized_text": original_text,
                "keywords_added": [],
                "keywords_kept": [],
            }

    async def optimize_full_resume(
        self, snapshot: dict, target_keywords: list[str],
    ) -> list[dict]:
        results = []
        sections = [
            (
                "summary",
                snapshot.get("profile", {}).get("bio", "")
                or snapshot.get("summary", ""),
            ),
        ]
        for exp in snapshot.get("experience", []):
            if exp.get("description"):
                sections.append((
                    f"experience_{exp.get('company', 'unknown')}",
                    exp["description"],
                ))
        for proj in snapshot.get("projects", []):
            if proj.get("description"):
                sections.append((
                    f"project_{proj.get('name', 'unknown')}",
                    proj["description"],
                ))
        sections.append((
            "skills",
            ", ".join(s.get("name", "") for s in snapshot.get("skills", [])),
        ))

        context = {
            "job_title": snapshot.get("profile", {}).get("headline", ""),
            "full_name": snapshot.get("profile", {}).get("full_name", ""),
        }
        for section_name, section_text in sections:
            if not section_text.strip():
                continue
            result = await self.optimize_section(
                section_name, section_text, target_keywords, context,
            )
            results.append(result)
        return results
