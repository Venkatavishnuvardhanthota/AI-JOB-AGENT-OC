import contextlib
import logging
from datetime import datetime
from typing import Any

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class RemoteOKProvider(BaseProvider):
    """Provider for RemoteOK job listings via their public API."""

    @property
    def name(self) -> str:
        return "remoteok"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search RemoteOK for jobs. Uses their public JSON API."""
        try:
            data = await self._get_json(f"{self.settings.base_url}/api")
        except Exception:
            logger.warning("RemoteOK API request failed")
            return []

        return self._parse_jobs(data, query)

    def _parse_jobs(self, data: Any, query: str) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        query_lower = query.lower()

        job_list = data if isinstance(data, list) else []
        for item in job_list:
            if not isinstance(item, dict):
                continue
            try:
                title = item.get("position", "Unknown")
                if query and query_lower not in title.lower():
                    continue

                company = item.get("company", "Unknown")
                description = item.get("description", "")
                if description:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(description, "lxml")
                    description = soup.get_text(separator="\n", strip=True)[:10000]

                url = item.get("url")
                apply_url = item.get("apply_url") or url

                location = item.get("location")
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                currency = item.get("currency", "USD")
                job_type = item.get("type")

                date_str = item.get("date")
                posted_at = None
                if date_str:
                    with contextlib.suppress(ValueError, TypeError):
                        posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

                tags = item.get("tags", [])
                if isinstance(tags, list):
                    tags = [t for t in tags if isinstance(t, str)]

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    description=description,
                    location=location,
                    url=url,
                    source_job_id=str(item.get("id", "")) if item.get("id") else None,
                    salary_min=float(salary_min) if salary_min else None,
                    salary_max=float(salary_max) if salary_max else None,
                    salary_currency=currency,
                    salary_period="yearly",
                    posted_at=posted_at,
                    job_type=job_type,
                    remote=True,
                    apply_url=apply_url,
                    skills=tags,
                    categories=tags,
                    raw={"source": "remoteok", "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse RemoteOK job")

        return jobs
