import logging

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class WellfoundProvider(BaseProvider):
    """Provider for Wellfound (AngelList) job search via scraping."""

    @property
    def name(self) -> str:
        return "wellfound"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Wellfound for jobs matching the query."""
        params: dict[str, str] = {"q": query}
        if kwargs.get("remote_only"):
            params["remote"] = "true"

        try:
            html = await self._get_html(
                f"{self.settings.base_url}/jobs",
                params=params,
            )
        except Exception:
            logger.warning("Wellfound scraping failed, returning empty results")
            return []

        return self._parse_search_results(html, query)

    def _parse_search_results(self, html: str, query: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []

        for card in soup.select("[data-testid='job-card'], .styles_jobCard__content, .job-card"):
            try:
                title_el = card.select_one("h2, h3, .styles_jobTitle__title")
                company_el = card.select_one(".styles_companyName__name, .company-name, a[href*='/company/']")
                location_el = card.select_one("[data-testid='job-card-location'], .styles_location__text")
                url_el = card.select_one("a[href*='/jobs/']")
                salary_el = card.select_one("[data-testid='job-card-salary'], .styles_salary__text")

                title = title_el.get_text(strip=True) if title_el else "Unknown"
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                location = location_el.get_text(strip=True) if location_el else None
                salary_text = salary_el.get_text(strip=True) if salary_el else None

                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href:
                        url = href if href.startswith("http") else f"https://wellfound.com{href}"

                salary_min = salary_max = currency = period = None
                if salary_text:
                    salary_min, salary_max, currency, period = self._parse_salary(salary_text)

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    location=location,
                    url=url,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency,
                    salary_period=period,
                    remote="remote" in (location or "").lower(),
                    raw={"source": "wellfound", "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Wellfound job card")

        return jobs

    def _parse_salary(self, text: str) -> tuple:
        import re

        text = text.replace(",", "").replace("$", "")
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        currency = "USD"
        period = "yearly"
        if "hour" in text.lower():
            period = "hourly"
        elif "month" in text.lower():
            period = "monthly"
        elif "year" in text.lower() or "annual" in text.lower():
            period = "yearly"

        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1]), currency, period
        if len(numbers) == 1:
            return float(numbers[0]), None, currency, period
        return None, None, None, None
