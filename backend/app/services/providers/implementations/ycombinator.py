import contextlib
import logging
from typing import Any

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class YCombinatorProvider(BaseProvider):
    """Provider for Y Combinator Work at a Startup jobs."""

    @property
    def name(self) -> str:
        return "ycombinator"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Y Combinator jobs."""
        params: dict[str, str] = {"query": query}
        if kwargs.get("location"):
            params["location"] = kwargs["location"]
        if kwargs.get("remote_only"):
            params["remote"] = "true"

        try:
            data = await self._get_json(
                f"{self.settings.base_url}/api/v1/jobs",
                params=params,
            )
        except Exception:
            logger.warning("Y Combinator search failed, returning empty results")
            return []

        return self._parse_jobs(data, query)

    def _parse_jobs(self, data: Any, query: str) -> list[RawJobData]:
        jobs: list[RawJobData] = []

        job_list = []
        if isinstance(data, dict):
            job_list = data.get("jobs", data.get("data", []))
        elif isinstance(data, list):
            job_list = data

        for item in job_list:
            if not isinstance(item, dict):
                continue
            try:
                title = item.get("title") or item.get("job_title", "Unknown")
                company = item.get("company_name") or item.get("company", {}).get("name", "Unknown")
                description = item.get("description") or item.get("job_description", "")
                location = item.get("location") or item.get("job_location")
                url = item.get("url") or item.get("apply_url") or item.get("job_url")
                apply_url = item.get("apply_url") or url

                salary_min = item.get("salary_min") or item.get("salary_minimum")
                salary_max = item.get("salary_max") or item.get("salary_maximum")
                salary_currency = item.get("salary_currency", "USD")
                salary_period = item.get("salary_period", "yearly")

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

                job_type = item.get("job_type") or item.get("employment_type")
                remote_val = item.get("remote") or item.get("remote_ok", False)
                if isinstance(remote_val, str):
                    remote_val = remote_val.lower() in ("true", "yes", "remote")

                posted_at_str = item.get("created_at") or item.get("posted_at") or item.get("date")
                posted_at = None
                if posted_at_str:
                    from datetime import datetime
                    with contextlib.suppress(ValueError, TypeError):
                        posted_at = datetime.fromisoformat(
                            posted_at_str.replace("Z", "+00:00")
                        )

                skills = item.get("skills", [])
                if isinstance(skills, str):
                    skills = [s.strip() for s in skills.split(",") if s.strip()]

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    description=description,
                    location=location,
                    url=url,
                    source_job_id=str(item.get("id", "")) if item.get("id") else None,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=salary_currency,
                    salary_period=salary_period,
                    posted_at=posted_at,
                    job_type=job_type,
                    remote=bool(remote_val),
                    apply_url=apply_url,
                    skills=skills if isinstance(skills, list) else [],
                    raw={"source": "ycombinator", "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Y Combinator job")

        return jobs
