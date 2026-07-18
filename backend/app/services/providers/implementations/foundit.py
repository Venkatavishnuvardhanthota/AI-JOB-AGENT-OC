import logging
import re
from datetime import datetime

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class FounditProvider(BaseProvider):
    """Provider for Foundit (formerly Monster India / Monster Gulf) job search via scraping."""

    @property
    def name(self) -> str:
        return "foundit"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Foundit for jobs matching the query."""
        params: dict[str, str] = {"q": query}
        if kwargs.get("location"):
            params["city"] = kwargs["location"]

        try:
            html = await self._get_html(
                f"{self.settings.base_url}/jobs",
                params=params,
            )
        except Exception:
            logger.warning("Foundit search failed, returning empty results")
            return []

        return self._parse_search_results(html, query)

    def _parse_search_results(self, html: str, query: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []

        for card in soup.select(
            ".job-card, .card, .job-tile, [data-cy='jobCard'], .job-list-item, article"
        ):
            try:
                title_el = card.select_one(
                    "h2 a, h3 a, .title a, [class*='title'] a, .job-title"
                )
                company_el = card.select_one(
                    ".company-name, .company, [class*='company'], .name"
                )
                location_el = card.select_one(
                    ".location, [class*='location'], .loc, .job-location"
                )
                salary_el = card.select_one(
                    ".salary, .sal, [class*='salary'], [class*='sal'], .job-salary, .package"
                )
                experience_el = card.select_one(
                    ".experience, .exp, [class*='exp'], .job-experience"
                )
                skill_els = card.select(".skill, .tag, [class*='skill'], .skill-tag")
                date_el = card.select_one(
                    ".date, .time, .posted, [class*='date'], [class*='posted']"
                )
                desc_el = card.select_one(
                    ".description, .desc, .job-description, [class*='desc']"
                )

                title = title_el.get_text(strip=True) if title_el else "Unknown"
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                location = location_el.get_text(strip=True) if location_el else None

                salary_text = salary_el.get_text(strip=True) if salary_el else None
                salary_min = salary_max = currency = period = None
                if salary_text:
                    salary_min, salary_max, currency, period = self._parse_salary(salary_text)

                skills = [
                    s.get_text(strip=True) for s in skill_els if s.get_text(strip=True)
                ]

                date_text = date_el.get_text(strip=True) if date_el else None
                posted_at = self._parse_date(date_text) if date_text else None

                experience = experience_el.get_text(strip=True) if experience_el else None

                description = desc_el.get_text(strip=True) if desc_el else None

                url_el = title_el or card.select_one("a[href*='/job/'], a[href*='/jobs/']")
                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href:
                        url = href if href.startswith("http") else f"https://www.foundit.in{href}"

                job_type = None
                if experience:
                    if "intern" in experience.lower():
                        job_type = "internship"
                    elif "fresher" in experience.lower():
                        job_type = "entry-level"

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    description=description,
                    location=location,
                    url=url,
                    source_job_id=self._extract_job_id(card),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency or "INR",
                    salary_period=period,
                    posted_at=posted_at,
                    job_type=job_type,
                    remote="remote" in (location or "").lower() or "work from home" in (location or "").lower(),
                    apply_url=url,
                    skills=skills,
                    raw={
                        "source": "foundit", "query": query,
                        "experience": experience,
                    },
                ))
            except Exception:
                logger.exception("Failed to parse Foundit job card")

        return jobs

    def _extract_job_id(self, card) -> str | None:
        job_id = card.get("data-job-id") or card.get("data-id") or card.get("id")
        if job_id:
            return str(job_id)
        url_el = card.select_one("a[href*='/job/']")
        if url_el:
            href = url_el.get("href", "")
            match = re.search(r"/job[s]?[/-](\d+)", href)
            if match:
                return match.group(1)
        return None

    def _parse_salary(self, text: str) -> tuple:
        text = text.replace(",", "").replace("₹", "").replace("Rs ", "")
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        currency = "INR"
        period = "yearly"
        if "hour" in text.lower() or "hr" in text.lower():
            period = "hourly"
        elif "month" in text.lower():
            period = "monthly"
        elif "year" in text.lower() or "annual" in text.lower() or "lac" in text.lower():
            period = "yearly"

        if len(numbers) >= 2:
            values = [float(n) for n in numbers[:2]]
            if "lac" in text.lower() or "lakh" in text.lower():
                values = [v * 100000 for v in values]
            return values[0], values[1], currency, period
        if len(numbers) == 1:
            val = float(numbers[0])
            if "lac" in text.lower() or "lakh" in text.lower():
                val *= 100000
            return val, None, currency, period
        return None, None, None, None

    def _parse_date(self, text: str | None) -> datetime | None:
        if not text:
            return None
        text = text.lower().strip()
        now = datetime.utcnow()

        if "just" in text or "now" in text or "today" in text:
            return now
        if "hour" in text or "hr" in text:
            numbers = re.findall(r"\d+", text)
            hours = int(numbers[0]) if numbers else 0
            from datetime import timedelta
            return now - timedelta(hours=hours)
        if "day" in text:
            numbers = re.findall(r"\d+", text)
            days = int(numbers[0]) if numbers else 0
            from datetime import timedelta
            return now - timedelta(days=days)
        if "week" in text:
            numbers = re.findall(r"\d+", text)
            weeks = int(numbers[0]) if numbers else 0
            from datetime import timedelta
            return now - timedelta(weeks=weeks)
        if "month" in text:
            numbers = re.findall(r"\d+", text)
            months = int(numbers[0]) if numbers else 1
            from datetime import timedelta
            return now - timedelta(days=months * 30)
        return None
