import logging
from typing import Any

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class WorkdayProvider(BaseProvider):
    """Provider for Workday job postings.

    Workday instances are per-company with custom URLs. Configure the
    base_url and API path via extra_params.
    """

    @property
    def name(self) -> str:
        return "workday"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Workday for jobs. Uses company-specific Workday instance."""
        company = kwargs.get("company") or self.settings.extra_params.get("company", "")
        api_path = kwargs.get("api_path") or self.settings.extra_params.get(
            "api_path",
            "/api/v1/tenant/company/job-postings",
        )

        if not self.settings.base_url and not company:
            logger.warning("Workday provider not configured (no base_url or company)")
            return []

        base = self.settings.base_url or f"https://{company}.wd5.myworkdayjobs.com"
        url = f"{base}{api_path}"

        try:
            data = await self._get_json(url, params={"q": query, "limit": "50"})
        except Exception:
            logger.warning("Workday search failed for company '%s'", company or base)
            return []

        return self._parse_jobs(data, query, company or base)

    def _parse_jobs(self, data: Any, query: str, source_id: str) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        query_lower = query.lower()

        job_list = []
        if isinstance(data, dict):
            job_list = data.get("jobPostings", data.get("jobs", data.get("items", [])))
        elif isinstance(data, list):
            job_list = data

        for job_data in job_list:
            if not isinstance(job_data, dict):
                continue
            try:
                title = job_data.get("title") or job_data.get("jobTitle", "Unknown")
                if query and query_lower not in title.lower():
                    continue

                company = job_data.get("company") or job_data.get("companyName") or source_id.title()

                location = job_data.get("location") or None
                if isinstance(location, dict):
                    location = location.get("name") or location.get("descriptor")

                description = (job_data.get("description") or job_data.get("jobDescription") or "")
                if description:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(description, "lxml")
                    description = soup.get_text(separator="\n", strip=True)[:10000]

                url = job_data.get("url") or job_data.get("externalPath") or job_data.get("applyUrl")

                salary_min = salary_max = None
                compensation = job_data.get("compensation") or job_data.get("payRate")
                if isinstance(compensation, dict):
                    salary_min = compensation.get("minimum") or compensation.get("min")
                    salary_max = compensation.get("maximum") or compensation.get("max")

                remote = "remote" in (location or "").lower()

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    description=description,
                    location=location,
                    url=url,
                    source_job_id=str(job_data.get("id", "")) if job_data.get("id") else None,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="USD",
                    salary_period="yearly",
                    remote=remote,
                    apply_url=url,
                    raw={"source": "workday", "company": source_id, "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Workday job posting")

        return jobs
