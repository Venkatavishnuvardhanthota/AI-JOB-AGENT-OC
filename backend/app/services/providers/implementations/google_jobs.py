import logging

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class GoogleJobsProvider(BaseProvider):
    """Provider for Google Jobs search results via scraping."""

    @property
    def name(self) -> str:
        return "google_jobs"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Google Jobs."""
        params: dict[str, str] = {
            "q": f"{query} jobs",
            "ibp": "htl;jobs",
            "hl": "en",
        }
        if kwargs.get("location"):
            params["q"] = f"{query} jobs in {kwargs['location']}"

        try:
            html = await self._get_html(
                self.settings.base_url,
                params=params,
            )
        except Exception:
            logger.warning("Google Jobs scraping failed, returning empty results")
            return []

        return self._parse_search_results(html, query)

    def _parse_search_results(self, html: str, query: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []

        for card in soup.select("[jsname='LgkLJd'], .job-card, [role='listitem']"):
            try:
                title_el = card.select_one("h3, .jobTitle, [aria-label*='title']")
                company_el = card.select_one(".company, [aria-label*='company'], .job-company")
                location_el = card.select_one(".location, [aria-label*='location']")
                url_el = card.select_one("a[href]")

                title = title_el.get_text(strip=True) if title_el else "Unknown"
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                location = location_el.get_text(strip=True) if location_el else None

                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href.startswith("/"):
                        url = f"https://www.google.com{href}"
                    elif href.startswith("http"):
                        url = href

                via_el = card.select_one(".via-info, .job-via")
                categories = []
                if via_el:
                    via_text = via_el.get_text(strip=True)
                    if via_text:
                        categories.append(via_text)

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    location=location,
                    url=url,
                    remote="remote" in (location or "").lower(),
                    categories=categories,
                    raw={"source": "google_jobs", "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Google Jobs card")

        return jobs
