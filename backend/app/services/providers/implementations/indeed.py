import logging
from datetime import datetime

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class IndeedProvider(BaseProvider):
    """Provider for Indeed job search via scraping."""

    @property
    def name(self) -> str:
        return "indeed"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Indeed for jobs matching the query."""
        location = kwargs.get("location", "")
        params: dict[str, str] = {"q": query}
        if location:
            params["l"] = location
        if kwargs.get("remote_only"):
            params["sc"] = "0kf:attr(DSQF7);"

        html = await self._get_html(
            f"{self.settings.base_url}/jobs",
            params=params,
        )
        return self._parse_search_results(html, query)

    def _parse_search_results(self, html: str, query: str) -> list[RawJobData]:
        """Parse Indeed search results HTML into RawJobData list."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []

        for card in soup.select(".job_seen_beacon, .jobsearch-SerpJobCard, .slider_item"):
            try:
                title_el = card.select_one(".jobTitle a, .jobTitle span, a.jobtitle")
                company_el = card.select_one(".companyName, .company, [data-testid='company-name']")
                location_el = card.select_one(".companyLocation, .location")
                url_el = card.select_one("a.jobtitle, a[id^='job_']")
                salary_el = card.select_one(".salary-snippet, .salaryText, .metadata.salary")
                date_el = card.select_one(".date, .date-a11y")

                title = title_el.get_text(strip=True) if title_el else "Unknown"
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                location = location_el.get_text(strip=True) if location_el else None

                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href.startswith("/"):
                        url = f"{self.settings.base_url}{href}"
                    elif href.startswith("http"):
                        url = href

                salary = salary_el.get_text(strip=True) if salary_el else None
                s_min, s_max, currency, period = (
                    self._parse_salary(salary) if salary else (None, None, None, None)
                )
                salary_min, salary_max = s_min, s_max

                date_text = date_el.get_text(strip=True) if date_el else None
                posted_at = self._parse_date(date_text) if date_text else None

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
                    raw={"source": "indeed", "query": query},
                ))
            except Exception:
                logger.exception("Failed to parse Indeed job card")

        return jobs

    def _parse_salary(self, text: str) -> tuple[float | None, float | None, str | None, str | None]:
        """Parse salary text like '$50,000 - $70,000 a year'."""
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

    def _parse_date(self, text: str) -> datetime | None:
        """Parse relative date strings like '3 days ago', '30+ days ago'."""
        import re

        text = text.lower().strip()
        now = datetime.utcnow()

        if "just posted" in text or "today" in text:
            return now
        if "hour" in text:
            return now
        if "day" in text:
            days = re.findall(r"\d+", text)
            if days:
                return now
        if "week" in text:
            weeks = re.findall(r"\d+", text)
            if weeks:
                return now
        if "month" in text:
            return now
        return None
