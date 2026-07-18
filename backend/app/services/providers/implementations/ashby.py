import logging
from typing import Any

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class AshbyProvider(BaseProvider):
    """Provider for Ashby job postings via their public API."""

    @property
    def name(self) -> str:
        return "ashby"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Ashby for jobs. Uses Ashby's public posting API."""
        company = kwargs.get("company") or self.settings.extra_params.get("company", "example")

        try:
            data = await self._get_json(f"{self.settings.base_url}/{company}")
        except Exception:
            logger.warning("Ashby search failed for company '%s'", company)
            return []

        return self._parse_jobs(data, query, company)

    def _parse_jobs(self, data: Any, query: str, company: str) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        query_lower = query.lower()

        if isinstance(data, dict):
            job_list = data.get("jobs", [])
        elif isinstance(data, list):
            job_list = data
        else:
            return jobs

        for job_data in job_list:
            if isinstance(job_data, dict):
                pass
            elif isinstance(job_data, str):
                continue
            else:
                continue

            try:
                title = job_data.get("title", "Unknown")
                if query and query_lower not in title.lower():
                    continue

                location = None
                location_obj = job_data.get("location")
                if isinstance(location_obj, dict):
                    location = location_obj.get("name")

                description = job_data.get("descriptionHtml") or job_data.get("descriptionPlain")
                if description:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(description, "lxml")
                    description = soup.get_text(separator="\n", strip=True)[:10000]

                salary_min = salary_max = None
                compensation = job_data.get("compensation")
                if isinstance(compensation, dict):
                    salary_min = compensation.get("min")
                    salary_max = compensation.get("max")
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

                url = job_data.get("jobUrl") or job_data.get("applyUrl")
                department = None
                department_obj = job_data.get("department")
                if isinstance(department_obj, dict):
                    department = department_obj.get("name")

                jobs.append(RawJobData(
                    title=title,
                    company_name=company.title(),
                    description=description,
                    location=location,
                    url=url,
                    source_job_id=str(job_data.get("id")) if job_data.get("id") else None,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="USD",
                    salary_period="yearly",
                    remote="remote" in (location or "").lower(),
                    apply_url=url,
                    categories=[department] if department else [],
                    raw={"source": "ashby", "company": company, "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Ashby job posting")

        return jobs
