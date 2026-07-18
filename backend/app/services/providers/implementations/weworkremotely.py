import logging

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class WeWorkRemotelyProvider(BaseProvider):
    """Provider for We Work Remotely job listings via scraping."""

    @property
    def name(self) -> str:
        return "weworkremotely"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search We Work Remotely."""
        category = kwargs.get("category", "remote-full-time-jobs")

        try:
            html = await self._get_html(f"{self.settings.base_url}/categories/{category}")
        except Exception:
            logger.warning("We Work Remotely scraping failed")
            return []

        return self._parse_search_results(html, query)

    def _parse_search_results(self, html: str, query: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []
        query_lower = query.lower()

        for li in soup.select("ul li, .job, article"):
            title_el = li.select_one("span.title, .title, h2 a, h3 a")
            if not title_el:
                continue

            try:
                title = title_el.get_text(strip=True)
                if query and query_lower not in title.lower():
                    continue

                company_el = li.select_one("span.company, .company, .listing-header a")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                url_el = title_el if title_el.name == "a" else li.select_one(
                    "a[href*='/jobs/'], a[href*='/remote-jobs/']"
                )
                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href.startswith("/"):
                        url = f"{self.settings.base_url}{href}"
                    elif href.startswith("http"):
                        url = href

                location_el = li.select_one(".region, .location, .meta")
                location = location_el.get_text(strip=True) if location_el else "Remote"

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    location=location if location != "Remote" else None,
                    url=url,
                    remote=True,
                    raw={"source": "weworkremotely", "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse WWR job listing")

        return jobs
