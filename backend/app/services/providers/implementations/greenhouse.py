import contextlib
import logging
from typing import Any

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class GreenhouseProvider(BaseProvider):
    """Provider for Greenhouse job boards via their public API."""

    @property
    def name(self) -> str:
        return "greenhouse"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Greenhouse job boards. Uses Greenhouse public board API."""
        board_token = kwargs.get("board_token") or self.settings.extra_params.get("board_token", "example")
        content = kwargs.get("content", True)

        try:
            data = await self._get_json(
                f"{self.settings.base_url}/{board_token}/jobs",
                params={"content": str(content).lower()},
            )
        except Exception:
            logger.warning("Greenhouse search failed for board '%s'", board_token)
            return []

        return self._parse_jobs(data, query, board_token)

    def _parse_jobs(self, data: dict[str, Any], query: str, board_token: str) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        query_lower = query.lower()

        for job_data in data.get("jobs", []):
            try:
                title = job_data.get("title", "Unknown")
                if query and query_lower not in title.lower():
                    continue

                offices = job_data.get("offices", [])
                location = None
                if offices:
                    location = ", ".join(
                        o.get("name", "") for o in offices if o.get("name")
                    )

                metadata_list = job_data.get("metadata", [])
                salary_min = salary_max = None
                for m in metadata_list:
                    if "min" in (m.get("name", "") or "").lower():
                        with contextlib.suppress(ValueError, TypeError):
                            salary_min = float(m.get("value", 0))
                    if "max" in (m.get("name", "") or "").lower():
                        with contextlib.suppress(ValueError, TypeError):
                            salary_max = float(m.get("value", 0))

                absolute_url = job_data.get("absolute_url")
                internal_job_id = job_data.get("internal_job_id")

                description = None
                if job_data.get("content"):
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(job_data["content"], "lxml")
                    description = soup.get_text(separator="\n", strip=True)[:10000]

                jobs.append(RawJobData(
                    title=title,
                    company_name=job_data.get("company_name") or board_token.title(),
                    description=description,
                    location=location,
                    url=absolute_url,
                    source_job_id=str(internal_job_id) if internal_job_id else None,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency="USD",
                    salary_period="yearly",
                    remote="remote" in (location or "").lower(),
                    apply_url=absolute_url,
                    raw={"source": "greenhouse", "board_token": board_token, "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Greenhouse job")

        return jobs
