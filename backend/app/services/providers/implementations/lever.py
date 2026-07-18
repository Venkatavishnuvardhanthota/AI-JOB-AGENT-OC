import logging
from typing import Any

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class LeverProvider(BaseProvider):
    """Provider for Lever job postings via their public API."""

    @property
    def name(self) -> str:
        return "lever"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Lever for jobs. Uses Lever's public posting API."""
        company = kwargs.get("company") or self.settings.extra_params.get("company", "example")

        try:
            data = await self._get_json(f"{self.settings.base_url}/{company}?mode=json")
        except Exception:
            logger.warning("Lever search failed for company '%s'", company)
            return []

        return self._parse_jobs(data, query, company)

    def _parse_jobs(self, data: Any, query: str, company: str) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        query_lower = query.lower()

        postings = data if isinstance(data, list) else []
        for posting in postings:
            try:
                title = posting.get("text", "Unknown")
                if query and query_lower not in title.lower():
                    continue

                categories = posting.get("categories", {}) or {}
                cats = posting.get("categories", {})
                location = cats.get("location") if isinstance(cats, dict) else None
                commitment = categories.get("commitment") if isinstance(categories, dict) else None
                team = categories.get("team") if isinstance(categories, dict) else None

                description = posting.get("description", "")

                salary_min = posting.get("salaryMin")
                salary_max = posting.get("salaryMax")
                if salary_min is not None:
                    try:
                        salary_min = float(salary_min)
                    except (ValueError, TypeError):
                        salary_min = None
                if salary_max is not None:
                    try:
                        salary_max = float(salary_max)
                    except (ValueError, TypeError):
                        salary_max = None

                url = posting.get("hostedUrl")

                job_type = None
                if commitment:
                    job_type = commitment.lower()

                skills = []
                if description:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(description, "lxml")
                    description = soup.get_text(separator="\n", strip=True)[:10000]

                lists = posting.get("lists", [])
                for lst in lists:
                    text = (lst.get("text", "") or "").lower()
                    if "requirement" in text:
                        requirements = [
                            item.get("content", "") for item in lst.get("content", [])
                        ]
                        skills.extend(requirements)

                jobs.append(RawJobData(
                    title=title,
                    company_name=company.title(),
                    description=description,
                    location=location,
                    url=url,
                    source_job_id=posting.get("id"),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="USD",
                    salary_period="yearly",
                    job_type=job_type,
                    remote="remote" in (location or "").lower(),
                    apply_url=url,
                    skills=skills,
                    categories=[team] if team else [],
                    raw={"source": "lever", "company": company, "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Lever posting")

        return jobs
