import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview_prep import InterviewPrep
from app.schemas.llm import LLMMessage, LLMRequest
from app.services.llm.factory import get_llm_client

logger = logging.getLogger(__name__)


class InterviewPrepService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate(
        self,
        user_id: uuid.UUID,
        job_title: str,
        company_name: str,
        job_description: str,
        resume_snapshot: dict | None = None,
        company_research: dict | None = None,
        include_behavioral: bool = True,
        include_technical: bool = True,
        include_salary: bool = True,
        include_notice_period: bool = True,
        include_strengths_weaknesses: bool = True,
        include_career_goals: bool = True,
        include_company_specific: bool = True,
    ) -> InterviewPrep:
        client = get_llm_client()

        resume_context = self._build_resume_context(resume_snapshot)
        company_context = self._build_company_context(company_research)

        behavioral_questions = []
        technical_questions = []
        salary_data = None
        notice_data = None
        strengths_data = []
        weaknesses_data = []
        career_data = None
        company_specific_data = []

        if include_behavioral:
            behavioral_questions = await self._generate_behavioral(
                client, job_title, company_name, job_description,
                resume_context, company_context,
            )

        if include_technical:
            technical_questions = await self._generate_technical(
                client, job_title, job_description, resume_context,
            )

        if include_salary:
            salary_data = await self._generate_salary(
                client, job_title, company_name, job_description,
                company_context,
            )

        if include_notice_period:
            notice_data = await self._generate_notice_period(client, resume_context)

        if include_strengths_weaknesses:
            sw_data = await self._generate_strengths_weaknesses(
                client, job_title, job_description, resume_context,
            )
            strengths_data = sw_data.get("strengths", [])
            weaknesses_data = sw_data.get("weaknesses", [])

        if include_career_goals:
            career_data = await self._generate_career_goals(
                client, job_title, company_name, job_description,
                resume_context, company_context,
            )

        if include_company_specific:
            company_specific_data = await self._generate_company_specific(
                client, company_name, job_description, company_context,
            )

        prep = InterviewPrep(
            user_id=user_id,
            job_title=job_title,
            company_name=company_name,
            behavioral_questions=behavioral_questions,
            technical_questions=technical_questions,
            salary_expectation=salary_data,
            notice_period=notice_data,
            strengths=strengths_data,
            weaknesses=weaknesses_data,
            career_goals=career_data,
            company_specific_answers=company_specific_data,
            is_active=True,
        )
        self.session.add(prep)
        await self.session.flush()
        await self.session.refresh(prep)
        return prep

    async def get(self, prep_id: uuid.UUID, user_id: uuid.UUID) -> InterviewPrep | None:
        stmt = select(InterviewPrep).where(
            InterviewPrep.id == prep_id,
            InterviewPrep.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[InterviewPrep]:
        stmt = (
            select(InterviewPrep)
            .where(InterviewPrep.user_id == user_id, InterviewPrep.is_active.is_(True))
            .order_by(InterviewPrep.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, prep_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(InterviewPrep).where(
            InterviewPrep.id == prep_id,
            InterviewPrep.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        prep = result.scalar_one_or_none()
        if not prep:
            return False
        await self.session.delete(prep)
        await self.session.flush()
        return True

    @staticmethod
    def _build_resume_context(snapshot: dict | None) -> str:
        if not snapshot:
            return "No resume data available."
        parts = []
        profile = snapshot.get("profile", {})
        if profile.get("headline"):
            parts.append(f"Headline: {profile['headline']}")
        if profile.get("bio"):
            parts.append(f"Bio: {profile['bio']}")
        skills = snapshot.get("skills", [])
        if skills:
            skill_names = [s.get("name", "") for s in skills if isinstance(s, dict)]
            if skill_names:
                parts.append(f"Skills: {', '.join(skill_names)}")
        experience = snapshot.get("experience", [])
        if experience:
            exp_summaries = []
            for exp in experience[:3]:
                if isinstance(exp, dict):
                    title = exp.get("title", "")
                    company = exp.get("company", "")
                    exp_summaries.append(f"{title} at {company}")
            if exp_summaries:
                parts.append(f"Experience: {' | '.join(exp_summaries)}")
        return " | ".join(parts) if parts else "No resume data available."

    @staticmethod
    def _build_company_context(research: dict | None) -> str:
        if not research:
            return "No company research data available."
        parts = []
        if research.get("industry"):
            parts.append(f"Industry: {research['industry']}")
        if research.get("mission"):
            parts.append(f"Mission: {research['mission']}")
        if research.get("values"):
            parts.append(f"Values: {', '.join(research['values'])}")
        if research.get("company_culture"):
            parts.append(f"Culture: {research['company_culture']}")
        if research.get("hiring_trends"):
            parts.append(f"Hiring: {'; '.join(research['hiring_trends'])}")
        if research.get("technology_stack"):
            parts.append(f"Tech Stack: {', '.join(research['technology_stack'])}")
        return " | ".join(parts) if parts else "No company research available."

    @staticmethod
    async def _call_llm_parse_json(
        client, system_prompt: str, user_prompt: str,
        temperature: float = 0.3, max_tokens: int = 2000,
    ) -> dict | list:
        if not client:
            return {}
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        try:
            response = await client.complete(request)
            parsed = json.loads(response.content)
            return parsed if isinstance(parsed, dict | list) else {}
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse LLM response: %s", e)
            return {}
        except Exception as e:
            logger.error("LLM call failed: %s", str(e))
            return {}

    async def _generate_behavioral(
        self, client, job_title, company_name, job_description,
        resume_context, company_context,
    ) -> list:
        system = (
            "You are an interview coach. Generate 5 behavioral interview questions "
            "with STAR (Situation, Task, Action, Result) method answers tailored to "
            "the candidate's resume and the job. Return a JSON array of objects with "
            "fields: question (string), situation (string), task (string), "
            "action (string), result (string), category (string: teamwork/leadership/"
            "problem-solving/conflict/adaptability)."
        )
        user = (
            f"Role: {job_title} at {company_name}\n"
            f"Job Description: {job_description}\n"
            f"Resume: {resume_context}\n"
            f"Company: {company_context}"
        )
        result = await self._call_llm_parse_json(client, system, user)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "questions" in result:
            return result["questions"]
        return []

    async def _generate_technical(
        self, client, job_title, job_description, resume_context,
    ) -> list:
        system = (
            "You are a technical interviewer. Generate 5 technical interview questions "
            "relevant to the job and candidate's background. Return a JSON array of "
            "objects with fields: question (string), topic (string like 'Python/System "
            "Design/Database'), difficulty (string: easy/medium/hard), answer (string, "
            "detailed), key_concepts (array of strings)."
        )
        user = (
            f"Role: {job_title}\n"
            f"Job Description: {job_description}\n"
            f"Resume: {resume_context}"
        )
        result = await self._call_llm_parse_json(client, system, user)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "questions" in result:
            return result["questions"]
        return []

    async def _generate_salary(
        self, client, job_title, company_name, job_description, company_context,
    ) -> dict:
        system = (
            "You are a salary research analyst. Provide salary expectations for the "
            "given role. Return a JSON object with fields: market_range_min (float), "
            "market_range_max (float), recommended (float), currency (string), "
            "factors (array of strings explaining what affects salary), "
            "negotiation_tips (array of strings)."
        )
        user = (
            f"Role: {job_title} at {company_name}\n"
            f"Job Description: {job_description}\n"
            f"Company Context: {company_context}"
        )
        result = await self._call_llm_parse_json(client, system, user, temperature=0.2)
        if isinstance(result, dict):
            return result
        return {}

    async def _generate_notice_period(
        self, client, resume_context,
    ) -> dict:
        system = (
            "You are a career advisor. Provide notice period guidance for the candidate. "
            "Return a JSON object with fields: current_period_weeks (int or null), "
            "negotiable (bool), negotiation_tips (array of strings), "
            "standard_in_industry (string)."
        )
        user = f"Candidate context: {resume_context}"
        result = await self._call_llm_parse_json(client, system, user, temperature=0.2)
        if isinstance(result, dict):
            return result
        return {}

    async def _generate_strengths_weaknesses(
        self, client, job_title, job_description, resume_context,
    ) -> dict:
        system = (
            "You are a career coach. Generate 3 strengths and 3 weaknesses for the "
            "candidate based on their resume and the target role. Return a JSON object "
            "with two keys: 'strengths' (array of objects with fields: strength (string), "
            "evidence (string), relevance_to_role (string), category (string: "
            "technical/soft-skill/leadership)), 'weaknesses' (array of objects with "
            "fields: weakness (string), improvement_plan (string), positive_framing "
            "(string), category (string: skill/experience/behavior))."
        )
        user = (
            f"Role: {job_title}\n"
            f"Job Description: {job_description}\n"
            f"Resume: {resume_context}"
        )
        result = await self._call_llm_parse_json(client, system, user)
        if isinstance(result, dict):
            return result
        return {"strengths": [], "weaknesses": []}

    async def _generate_career_goals(
        self, client, job_title, company_name, job_description,
        resume_context, company_context,
    ) -> dict:
        system = (
            "You are a career strategist. Generate career goals aligned with the role "
            "and company. Return a JSON object with fields: short_term (string, 1-2 "
            "sentences about next 1-2 years), long_term (string, 1-2 sentences about "
            "5+ years), alignment_with_company (string, how goals fit this company), "
            "timeline_years (int or null)."
        )
        user = (
            f"Role: {job_title} at {company_name}\n"
            f"Job Description: {job_description}\n"
            f"Resume: {resume_context}\n"
            f"Company: {company_context}"
        )
        result = await self._call_llm_parse_json(client, system, user)
        if isinstance(result, dict):
            return result
        return {}

    async def _generate_company_specific(
        self, client, company_name, job_description, company_context,
    ) -> list:
        system = (
            "You are an interview strategist. Generate 3 company-specific interview "
            "questions and tailored answers based on the company's profile. Return a "
            "JSON array of objects with fields: question (string, a question the "
            "interviewer might ask about this company), context (string, why this "
            "question matters), suggested_answer (string, a well-crafted response), "
            "research_source (string or null, where the info comes from)."
        )
        user = (
            f"Company: {company_name}\n"
            f"Job Description: {job_description}\n"
            f"Company Research: {company_context}"
        )
        result = await self._call_llm_parse_json(client, system, user)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "answers" in result:
            return result["answers"]
        return []
