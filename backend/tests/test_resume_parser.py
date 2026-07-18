import pytest

from app.services.resume_parser import ResumeParserService


@pytest.fixture
def parser():
    return ResumeParserService()


class TestResumeParser:
    def test_parse_email(self, parser):
        text = "John Doe\njohn.doe@example.com\nPhone: +1-555-1234"
        result = parser.parse_text(text)
        assert result.get("email") == "john.doe@example.com"

    def test_parse_phone(self, parser):
        text = "Contact: (555) 123-4567\njane@example.com"
        result = parser.parse_text(text)
        assert result.get("phone")

    def test_parse_name(self, parser):
        text = "Jane Smith\njane@example.com\nSoftware Engineer"
        result = parser.parse_text(text)
        assert result.get("full_name") == "Jane Smith"

    def test_parse_skills(self, parser):
        text = "Skills: Python, JavaScript, TypeScript, React, FastAPI"
        result = parser.parse_text(text)
        skills = result.get("skills", [])
        assert len(skills) >= 3
        names = [s["name"] for s in skills]
        assert "Python" in names

    def test_parse_education(self, parser):
        text = """
John Doe
john@example.com

Education
Bachelor of Science in Computer Science
MIT
2018 - 2022
GPA: 3.8

Experience
Software Engineer at Google
2022 - Present
"""
        result = parser.parse_text(text)
        education = result.get("education", [])
        assert len(education) > 0
        assert "MIT" in education[0].get("institution", "")

    def test_parse_experience(self, parser):
        text = """
Jane Doe
jane@example.com

Experience
Senior Developer
Acme Corp
2020 - Present
Led development of microservices architecture.
"""
        result = parser.parse_text(text)
        experience = result.get("experience", [])
        assert len(experience) > 0
        assert "Acme Corp" in experience[0].get("company", "")

    def test_parse_languages(self, parser):
        text = "Languages: English (Native), Spanish (Fluent), French (Basic)"
        result = parser.parse_text(text)
        languages = result.get("languages", [])
        assert len(languages) > 0

    def test_parse_certifications(self, parser):
        text = """
Certifications
AWS Certified Solutions Architect
Amazon Web Services
2023

Project Management Professional
PMI
2022
"""
        result = parser.parse_text(text)
        certs = result.get("certifications", [])
        assert len(certs) > 0

    def test_parse_linkedin_github(self, parser):
        text = """
John Doe
https://linkedin.com/in/johndoe
https://github.com/johndoe
"""
        result = parser.parse_text(text)
        assert result.get("linkedin_url")
        assert result.get("github_url")

    def test_parse_summary(self, parser):
        text = """
John Doe
john@example.com

Professional Summary
Experienced software engineer with 5 years of experience building scalable applications.

Skills
Python, Java
"""
        result = parser.parse_text(text)
        assert result.get("summary")
        assert "software engineer" in result["summary"].lower()

    def test_parse_projects(self, parser):
        text = """
Projects
E-commerce Platform
Built a full-stack e-commerce platform with React and FastAPI
https://github.com/user/ecommerce

Task Manager
A task management application
"""
        result = parser.parse_text(text)
        projects = result.get("projects", [])
        assert len(projects) > 0
