import json
import logging
import time
from threading import Lock
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_research import CompanyResearch
from app.schemas.llm import LLMMessage, LLMRequest
from app.services.llm.factory import get_llm_client

logger = logging.getLogger(__name__)


class _InMemoryCache:
    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        self._default_ttl = default_ttl_seconds
        self._store: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            expiry = self._expiry.get(key)
            if expiry is None:
                return None
            if time.monotonic() > expiry:
                self._store.pop(key, None)
                self._expiry.pop(key, None)
                return None
            return self._store.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or self._default_ttl
        with self._lock:
            self._store[key] = value
            self._expiry[key] = time.monotonic() + ttl

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._expiry.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._expiry.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)


class CompanyResearchService:
    def __init__(
        self,
        session: AsyncSession | None = None,
        cache: _InMemoryCache | None = None,
    ) -> None:
        self.session = session
        self._cache = cache or _InMemoryCache(default_ttl_seconds=3600)

    @staticmethod
    def _make_cache_key(company_name: str) -> str:
        return f"company_research:{company_name.strip().lower()}"

    async def research(self, company_name: str) -> dict:
        cache_key = self._make_cache_key(company_name)

        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("Memory cache hit for %s", company_name)
            return cached

        if self.session is not None:
            db_result = await self._get_from_db(company_name)
            if db_result is not None:
                logger.debug("DB cache hit for %s", company_name)
                data = self._model_to_dict(db_result)
                self._cache.set(cache_key, data)
                return data

        logger.info("Researching company: %s", company_name)
        client = get_llm_client()
        if not client:
            logger.warning("No LLM client available for company research")
            return self._fallback_info(company_name)

        try:
            result = await self._call_llm(client, company_name)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse company research for %s: %s", company_name, e)
            return self._fallback_info(company_name)
        except Exception as e:
            logger.error("Company research failed for %s: %s", company_name, str(e))
            return self._fallback_info(company_name)

        result["company_name"] = company_name
        result = self._sanitize_result(result, company_name)
        result["summary"] = self._generate_summary(result)

        self._cache.set(cache_key, result)

        if self.session is not None:
            await self._save_to_db(company_name, result)

        return result

    async def get_cached(self, company_name: str) -> dict | None:
        cache_key = self._make_cache_key(company_name)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        if self.session is not None:
            db_result = await self._get_from_db(company_name)
            if db_result is not None:
                data = self._model_to_dict(db_result)
                self._cache.set(cache_key, data)
                return data
        return None

    async def get_summary(self, company_name: str) -> str | None:
        data = await self.get_cached(company_name)
        if data is not None:
            if data.get("summary"):
                return data["summary"]
            summary = self._generate_summary(data)
            return summary
        result = await self.research(company_name)
        return result.get("summary")

    async def invalidate_cache(self, company_name: str) -> None:
        cache_key = self._make_cache_key(company_name)
        self._cache.delete(cache_key)
        if self.session is not None:
            stmt = select(CompanyResearch).where(
                CompanyResearch.company_name.ilike(company_name)
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if model is not None:
                await self.session.delete(model)
                await self.session.flush()

    async def _get_from_db(self, company_name: str) -> CompanyResearch | None:
        if self.session is None:
            return None
        stmt = select(CompanyResearch).where(
            CompanyResearch.company_name.ilike(company_name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _save_to_db(self, company_name: str, data: dict) -> None:
        if self.session is None:
            return
        try:
            stmt = select(CompanyResearch).where(
                CompanyResearch.company_name.ilike(company_name)
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            fields = {
                "industry": data.get("industry"),
                "mission": data.get("mission"),
                "values": data.get("values") or [],
                "products_or_services": data.get("products_or_services") or [],
                "company_culture": data.get("company_culture"),
                "recent_news": data.get("recent_news") or [],
                "headquarters": data.get("headquarters"),
                "company_size": data.get("company_size"),
                "linkedin_url": data.get("linkedin_url"),
                "hiring_trends": data.get("hiring_trends") or [],
                "technology_stack": data.get("technology_stack") or [],
                "funding": data.get("funding"),
                "summary": data.get("summary"),
            }

            if existing:
                for key, value in fields.items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                new_record = CompanyResearch(
                    company_name=company_name, **fields
                )
                self.session.add(new_record)
            await self.session.flush()
        except Exception as e:
            logger.warning("Failed to persist company research for %s: %s", company_name, e)

    @staticmethod
    def _model_to_dict(model: CompanyResearch) -> dict:
        return {
            "id": str(model.id),
            "company_name": model.company_name,
            "industry": model.industry,
            "mission": model.mission,
            "values": model.values or [],
            "products_or_services": model.products_or_services or [],
            "company_culture": model.company_culture,
            "recent_news": model.recent_news or [],
            "headquarters": model.headquarters,
            "company_size": model.company_size,
            "linkedin_url": model.linkedin_url,
            "hiring_trends": model.hiring_trends or [],
            "technology_stack": model.technology_stack or [],
            "funding": model.funding,
            "summary": model.summary,
            "cached_at": (
                model.cached_at.isoformat() if model.cached_at else None
            ),
        }

    async def _call_llm(self, client: Any, company_name: str) -> dict:
        system_prompt = (
            "You are a company research assistant. Given a company name, "
            "provide structured information about the company. "
            "Return valid JSON with these fields:\n"
            "- company_name (string)\n"
            "- industry (string, 1-2 words, or null)\n"
            "- mission (string, 1-2 sentences, or null)\n"
            "- values (list of 3-5 strings, or empty list)\n"
            "- products_or_services (list of strings, or empty list)\n"
            "- company_culture (string, 1-2 sentences, or null)\n"
            "- recent_news (list of 2-3 strings, short bullet points, or empty list)\n"
            "- headquarters (string, city/state or null)\n"
            "- company_size (string like '1000-5000' or null)\n"
            "- linkedin_url (string URL or null; do NOT make up URLs)\n"
            "- hiring_trends (list of 2-4 strings describing recent hiring patterns, "
            "or empty list)\n"
            "- technology_stack (list of 2-6 strings listing technologies used, "
            "or empty list)\n"
            "- funding (object with keys: total_funding (string like '$100M'), "
            "last_round (string like 'Series B'), "
            "last_round_date (string like '2024'), "
            "investors (list of strings), or null if not applicable)\n"
            "If you are unsure about any field, use null for scalars or "
            "empty list for lists. Do NOT make up data. "
            "Do NOT make up URLs. Use null for URLs you are not certain about."
        )
        user_prompt = f"Research the company: {company_name}"

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt),
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        response = await client.complete(request)
        parsed = json.loads(response.content)
        if not isinstance(parsed, dict):
            raise ValueError("Response was not a JSON object")
        return parsed

    @staticmethod
    def _sanitize_result(result: dict, company_name: str) -> dict:
        fields = {
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
            "hiring_trends": [],
            "technology_stack": [],
            "funding": None,
        }
        for key, default in fields.items():
            if key not in result or result[key] is None:
                result[key] = default
            elif isinstance(default, list) and not isinstance(result[key], list):
                if isinstance(result[key], str) and result[key].strip():
                    result[key] = [result[key]]
                else:
                    result[key] = []
        return result

    @staticmethod
    def _generate_summary(data: dict) -> str:
        parts = []
        company = data.get("company_name", "This company")
        industry = data.get("industry")
        if industry:
            parts.append(f"{company} operates in the {industry} industry.")
        mission = data.get("mission")
        if mission:
            parts.append(f"Its mission: {mission}")
        products = data.get("products_or_services")
        if products:
            count = len(products)
            if count == 1:
                parts.append(f"It offers: {products[0]}.")
            else:
                items = ", ".join(products[:-1]) + f" and {products[-1]}"
                parts.append(f"Its products/services include {items}.")
        culture = data.get("company_culture")
        if culture:
            parts.append(f"Culture: {culture}")
        tech = data.get("technology_stack")
        if tech:
            items = ", ".join(tech)
            parts.append(f"Technology stack includes {items}.")
        hiring = data.get("hiring_trends")
        if hiring:
            items = "; ".join(hiring)
            parts.append(f"Hiring trends: {items}")
        funding = data.get("funding")
        if funding and isinstance(funding, dict):
            total = funding.get("total_funding")
            if total:
                parts.append(f"Total funding: {total}.")
        if not parts:
            parts.append(f"{company} - no detailed information available.")
        return " ".join(parts)

    @staticmethod
    def _fallback_info(company_name: str) -> dict:
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
            "hiring_trends": [],
            "technology_stack": [],
            "funding": None,
            "summary": f"{company_name} - no detailed information available.",
        }
