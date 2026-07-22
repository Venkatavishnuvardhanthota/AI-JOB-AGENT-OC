from __future__ import annotations

COVER_LETTER_TEMPLATES: dict[str, dict[str, str]] = {
    "software_engineer": {
        "greeting": "Dear Hiring Manager{tone_suffix},",
        "opening": (
            "I am writing to express my strong interest in the {job_title} position at {company_name}. "
            "As a {career_level} software engineer with {years_experience} years of experience "
            "building {industry_focus} applications, I am confident that my technical expertise and "
            "problem-solving abilities would make me a valuable addition to your engineering team."
        ),
        "company": (
            "I have been following {company_name}'s work in {industry} and am particularly impressed "
            "by your team's commitment to {company_value}. My background in {technical_skills} aligns "
            "well with the technical challenges your team is tackling."
        ),
        "experience": (
            "In my previous role as {current_role}, I delivered several key achievements including "
            "{top_strength}. This experience has prepared me to hit the ground running in this role "
            "and contribute meaningfully from day one."
        ),
        "skills": (
            "My technical skill set includes {primary_skills_list}, which directly aligns with "
            "the requirements for this position. I have {matching_skills_count} of the key skills "
            "you are looking for, including {matching_skills_list}."
        ),
        "projects": (
            "I have worked on projects involving {project_list}, demonstrating my ability to "
            "deliver high-quality software solutions. These experiences have strengthened my "
            "skills in software architecture, system design, and collaborative development."
        ),
        "closing": (
            "I am excited about the opportunity to bring my expertise to {company_name} and "
            "would welcome the chance to discuss how my background aligns with your team's goals. "
            "Thank you for considering my application."
        ),
        "signature": "Sincerely,\n{user_name}",
    },
    "backend": {
        "greeting": "Dear Hiring Manager{tone_suffix},",
        "opening": (
            "I am writing to apply for the {job_title} position at {company_name}. "
            "With {years_experience} years of experience as a {career_level} backend engineer, "
            "I have a proven track record of building scalable, maintainable server-side systems."
        ),
        "company": (
            "{company_name}'s reputation in {industry} is impressive, and I am drawn to the "
            "engineering challenges your team faces. My experience with {technical_skills} would "
            "allow me to contribute immediately to your backend infrastructure."
        ),
        "experience": (
            "As a {current_role}, I have designed and implemented distributed systems, RESTful APIs, "
            "and data processing pipelines. One of my key accomplishments includes {top_strength}."
        ),
        "skills": (
            "My backend expertise spans {primary_skills_list}, with strong proficiency in "
            "database design, API development, and system architecture. "
            "I match {matching_skills_count} of the required skills for this role."
        ),
        "projects": (
            "I have delivered projects involving {project_list}, which required deep technical "
            "knowledge of backend systems, performance optimization, and scalability patterns."
        ),
        "closing": (
            "I would welcome the opportunity to discuss how my backend engineering experience "
            "can benefit {company_name}. Thank you for your time and consideration."
        ),
        "signature": "Sincerely,\n{user_name}",
    },
    "general": {
        "greeting": "Dear Hiring Manager{tone_suffix},",
        "opening": (
            "I am writing to express my interest in the {job_title} position at {company_name}. "
            "With {years_experience} years of experience as a {career_level} professional, "
            "I believe my skills and experience align well with the requirements of this role."
        ),
        "company": (
            "I admire {company_name}'s work in {industry} and am excited about the opportunity "
            "to contribute to your team's success. My background in {technical_skills} "
            "provides a strong foundation for this position."
        ),
        "experience": (
            "In my current role as {current_role}, I have developed expertise in delivering "
            "results and driving projects to completion. A key achievement includes {top_strength}."
        ),
        "skills": (
            "My professional skill set includes {primary_skills_list}, and I match "
            "{matching_skills_count} of the key qualifications you are seeking. "
            "I am confident these skills will enable me to excel in this role."
        ),
        "projects": (
            "Throughout my career, I have worked on projects involving {project_list}, "
            "which have strengthened my professional capabilities and problem-solving approach."
        ),
        "closing": (
            "I look forward to the possibility of discussing how my experience and skills "
            "can contribute to the continued success of {company_name}. "
            "Thank you for your consideration."
        ),
        "signature": "Sincerely,\n{user_name}",
    },
}


TONE_SUFFIXES: dict[str, str] = {
    "professional": "",
    "enthusiastic": " and Team",
    "formal": "",
    "casual": ", and Team",
}

LENGTH_CONFIG: dict[str, dict[str, bool]] = {
    "short": {"projects": False, "company": False},
    "medium": {"projects": True, "company": True},
    "long": {"projects": True, "company": True},
}


class TemplateEngine:
    def get_template(self, style: str) -> dict[str, str]:
        template = COVER_LETTER_TEMPLATES.get(style)
        if template:
            return template
        return COVER_LETTER_TEMPLATES["general"]

    def list_styles(self) -> list[str]:
        return list(COVER_LETTER_TEMPLATES.keys())

    def render(self, template_text: str, variables: dict[str, str]) -> str:
        result = template_text
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, value or "")
        return result

    def get_sections_for_length(self, length: str) -> list[str]:
        config = LENGTH_CONFIG.get(length, LENGTH_CONFIG["medium"])
        sections = ["greeting", "opening"]
        if config.get("company", True):
            sections.append("company")
        sections.append("experience")
        sections.append("skills")
        if config.get("projects", True):
            sections.append("projects")
        sections.append("closing")
        sections.append("signature")
        return sections
