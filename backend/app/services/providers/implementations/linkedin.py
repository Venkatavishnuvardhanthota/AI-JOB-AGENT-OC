import logging
from datetime import datetime

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class LinkedInProvider(BaseProvider):
    """Provider for LinkedIn job search via scraping."""

    @property
    def name(self) -> str:
        return "linkedin"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search LinkedIn for jobs matching the query."""
        location = kwargs.get("location", "")
        params: dict[str, str] = {
            "keywords": query,
            "f_AL": "true" if kwargs.get("remote_only") else "",
        }
        if location:
            params["location"] = location

        html = await self._get_html(
            f"{self.settings.base_url}/search",
            params=params,
        )
        return self._parse_search_results(html, query)

    def _parse_search_results(self, html: str, query: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []

        for card in soup.select(".base-card, .job-search-card, li[data-job-id]"):
            try:
                title_el = card.select_one(
                    ".base-search-card__title, h3 a, [data-anonymize='job-title']"
                )
                company_el = card.select_one(
                    ".base-search-card__subtitle, .job-card-container__company-name, h4 a"
                )
                location_el = card.select_one(
                    ".job-search-card__location, .base-search-card__metadata-item"
                )
                url_el = card.select_one("a.base-card__full-link, a[data-anonymize='job-title']")
                date_el = card.select_one(
                    ".job-search-card__listdate, .base-search-card__metadata-item time"
                )
                salary_el = card.select_one(".job-search-card__salary-info")

                title = title_el.get_text(strip=True) if title_el else "Unknown"
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                location = location_el.get_text(strip=True) if location_el else None

                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href:
                        url = href if href.startswith("http") else f"https://www.linkedin.com{href}"

                date_text = date_el.get_text(strip=True) if date_el else None
                posted_at = self._parse_relative_date(date_text) if date_text else None

                salary_text = salary_el.get_text(strip=True) if salary_el else None
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
                    posted_at=posted_at,
                    remote="remote" in (location or "").lower(),
                    raw={"source": "linkedin", "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse LinkedIn job card")

        return jobs

    def _parse_relative_date(self, text: str) -> datetime | None:
        text = text.lower().strip()
        now = datetime.utcnow()

        if "minute" in text or "min" in text:
            return now
        if "hour" in text:
            return now
        if "day" in text:
            return now
        if "week" in text or "month" in text:
            return now
        if "just now" in text or "recently" in text:
            return now
        return None

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
        elif "year" in text.lower():
            period = "yearly"

        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1]), currency, period
        if len(numbers) == 1:
            return float(numbers[0]), None, currency, period
        return None, None, None, None
