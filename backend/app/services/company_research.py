import json
import logging

from app.schemas.llm import LLMMessage, LLMRequest
from app.services.llm.factory import get_llm_client

logger = logging.getLogger(__name__)


class CompanyResearchService:
    async def research(self, company_name: str) -> dict:
        client = get_llm_client()
        if not client:
            logger.warning("No LLM client available for company research")
            return self._fallback_info(company_name)

        system_prompt = (
            "You are a company research assistant. Given a company name, "
            "provide structured information about the company. "
            "Return valid JSON with these fields: "
            "company_name, industry, mission (1-2 sentences), "
            "values (list of 3-5 strings), products_or_services (list), "
            "company_culture (1-2 sentences), recent_news (2-3 bullet points), "
            "headquarters, company_size (e.g., '1000-5000'), "
            "linkedin_url (if known). "
            "If you are unsure about any field, use null. "
            "Do NOT make up URLs. Use null for URLs you are not certain about."
        )
        user_prompt = f"Research the company: {company_name}"

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        try:
            response = await client.complete(request)
            parsed = json.loads(response.content)
            if not isinstance(parsed, dict):
                raise ValueError("Response was not a JSON object")
            return parsed
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse company research for %s: %s", company_name, e)
            return self._fallback_info(company_name)
        except Exception as e:
            logger.error("Company research failed for %s: %s", company_name, str(e))
            return self._fallback_info(company_name)

    def _fallback_info(self, company_name: str) -> dict:
        return {
            "company_name": company_name,
            "industry": None,
            "mission": None,
            "values": [],
            "products_or_services": [],
            "company_culture": None,
            "recent_news": [],
            "headquarters": None,
            "company_size": None,
            "linkedin_url": None,
        }
