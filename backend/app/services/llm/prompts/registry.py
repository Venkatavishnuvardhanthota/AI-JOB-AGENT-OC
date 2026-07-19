import logging
from datetime import datetime, timezone

from app.schemas.llm import PromptRenderResponse

logger = logging.getLogger(__name__)

BUILT_IN_PROMPTS: dict[str, list[dict]] = {
    "job-application-email": [
        {
            "version": 1,
            "template": (
                "Subject: Application for {{job_title}} at {{company_name}}\n\n"
                "Dear {{hiring_manager_name or 'Hiring Team'}},\n\n"
                "I am writing to express my strong interest in the {{job_title}} "
                "position at {{company_name}}. With my background in {{skill_area}}, "
                "I am confident that I would be a valuable addition to your team.\n\n"
                "{{custom_message}}\n\n"
                "I have attached my resume for your review and look forward to "
                "the opportunity to discuss how my experience aligns with the "
                "needs of {{company_name}}.\n\n"
                "Best regards,\n{{applicant_name}}"
            ),
            "variables": [
                "job_title", "company_name", "hiring_manager_name",
                "skill_area", "custom_message", "applicant_name",
            ],
            "description": "Template for job application email",
        },
    ],
    "cover-letter": [
        {
            "version": 1,
            "template": (
                "Dear {{hiring_manager_name or 'Hiring Team'}},\n\n"
                "I am excited to apply for the {{job_title}} role at {{company_name}}. "
                "As a {{current_role}} with {{years_experience}} years of experience "
                "in {{field}}, I have developed strong skills in {{key_skills}}.\n\n"
                "{{relevant_experience}}\n\n"
                "I am particularly drawn to {{company_name}} because {{reason_for_interest}}.\n\n"
                "Thank you for considering my application. I look forward to hearing from you.\n\n"
                "Sincerely,\n{{applicant_name}}"
            ),
            "variables": [
                "job_title", "company_name", "hiring_manager_name",
                "current_role", "years_experience", "field", "key_skills",
                "relevant_experience", "reason_for_interest", "applicant_name",
            ],
            "description": "Template for cover letter",
        },
    ],
    "skill-based-question": [
        {
            "version": 1,
            "template": (
                "Based on the job description for {{job_title}} at {{company_name}}, "
                "the key skills required are {{required_skills}}. The user's profile "
                "shows proficiency in {{user_skills}}.\n\n"
                "Please identify skills gaps and suggest learning resources or "
                "projects to bridge them. Consider the user's current experience "
                "level of {{experience_level}}."
            ),
            "variables": [
                "job_title", "company_name", "required_skills",
                "user_skills", "experience_level",
            ],
            "description": "Template for skill gap analysis",
        },
    ],
    "interview-prep": [
        {
            "version": 1,
            "template": (
                "Prepare interview questions and answers for the {{job_title}} "
                "position at {{company_name}}. The job requires {{key_requirements}}.\n\n"
                "The user has experience in {{user_experience}}. Generate:\n"
                "1. Technical questions relevant to {{job_title}}\n"
                "2. Behavioral questions based on the company's {{company_culture}}\n"
                "3. Suggested talking points highlighting {{user_strengths}}"
            ),
            "variables": [
                "job_title", "company_name", "key_requirements",
                "user_experience", "company_culture", "user_strengths",
            ],
            "description": "Template for interview preparation",
        },
    ],
}


class PromptRegistry:
    def __init__(self):
        self._prompts: dict[str, list[dict]] = {
            k: [dict(v, **{"_loaded_at": datetime.now(timezone.utc).isoformat()}) for v in vs]
            for k, vs in BUILT_IN_PROMPTS.items()
        }

    def get_prompt(self, name: str, version: int | None = None) -> dict | None:
        prompts = self._prompts.get(name)
        if not prompts:
            return None
        if version:
            for p in prompts:
                if p["version"] == version:
                    return p
            return None
        return max(prompts, key=lambda p: p["version"])

    def list_prompts(self) -> list[dict]:
        result = []
        for name, prompts in self._prompts.items():
            latest = max(prompts, key=lambda p: p["version"])
            result.append({
                "name": name,
                "latest_version": latest["version"],
                "description": latest.get("description", ""),
                "version_count": len(prompts),
            })
        return result

    def register_prompt(
        self,
        name: str,
        template: str,
        variables: list[str] | None = None,
        description: str | None = None,
    ) -> dict:
        existing = self._prompts.get(name, [])
        new_version = (max(p["version"] for p in existing) + 1) if existing else 1
        import re
        if variables is None:
            variables = sorted(set(re.findall(r"\{\{(\w+)\}\}", template)))
        entry = {
            "version": new_version,
            "template": template,
            "variables": variables,
            "description": description or "",
            "_loaded_at": datetime.now(timezone.utc).isoformat(),
        }
        self._prompts.setdefault(name, []).append(entry)
        return entry

    def render(self, name: str, variables: dict[str, str], version: int | None = None) -> PromptRenderResponse | None:
        prompt = self.get_prompt(name, version)
        if not prompt:
            return None
        rendered = prompt["template"]
        for key, value in variables.items():
            rendered = rendered.replace("{{" + key + "}}", value)
        return PromptRenderResponse(
            rendered=rendered,
            name=name,
            version=prompt["version"],
        )
