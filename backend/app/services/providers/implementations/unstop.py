import logging
import re
from datetime import datetime

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class UnstopProvider(BaseProvider):
    """Provider for Unstop (formerly Dare2Compete) opportunities via scraping."""

    @property
    def name(self) -> str:
        return "unstop"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Unstop for opportunities matching the query."""
        params: dict[str, str] = {"q": query}
        if kwargs.get("location"):
            params["city"] = kwargs["location"]

        endpoint = kwargs.get("type", "jobs")
        if endpoint not in ("jobs", "internships", "competitions"):
            endpoint = "jobs"

        try:
            html = await self._get_html(
                f"{self.settings.base_url}/explore/{endpoint}",
                params=params,
            )
        except Exception:
            logger.warning("Unstop search failed, returning empty results")
            return []

        return self._parse_search_results(html, query, endpoint)

    def _parse_search_results(self, html: str, query: str, opp_type: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []

        for card in soup.select(
            ".opportunity-card, .card, .listing-card, [class*='opportunity'], "
            "[class*='listing'], .job-card, article"
        ):
            try:
                title_el = card.select_one(
                    "h2 a, h3 a, .title a, [class*='title'] a, .heading a"
                )
                company_el = card.select_one(
                    ".company-name, .company, .organisation-name, [class*='company'], "
                    "[class*='organization'], [class*='org']"
                )
                location_el = card.select_one(
                    ".location, .loc, [class*='location'], .place"
                )
                stipend_el = card.select_one(
                    ".stipend, .salary, .prize, .reward, [class*='stipend'], "
                    "[class*='salary'], [class*='prize']"
                )
                skill_els = card.select(
                    ".skill, .tag, [class*='skill'], [class*='tag'], .badge"
                )
                date_el = card.select_one(
                    ".date, .posted, .time, [class*='date'], [class*='posted']"
                )
                desc_el = card.select_one(
                    ".description, .desc, [class*='description'], .text-content"
                )
                type_el = card.select_one(
                    ".type, .opportunity-type, .category, [class*='type'], [class*='category']"
                )

                title = title_el.get_text(strip=True) if title_el else "Unknown"
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                location = location_el.get_text(strip=True) if location_el else None

                stipend_text = stipend_el.get_text(strip=True) if stipend_el else None
                salary_min = salary_max = currency = period = None
                if stipend_text:
                    salary_min, salary_max, currency, period = self._parse_stipend(stipend_text)

                skills = [
                    s.get_text(strip=True) for s in skill_els if s.get_text(strip=True)
                ]

                date_text = date_el.get_text(strip=True) if date_el else None
                posted_at = self._parse_date(date_text) if date_text else None

                description = desc_el.get_text(strip=True) if desc_el else None

                opportunity_type = type_el.get_text(strip=True) if type_el else opp_type

                url_el = title_el or card.select_one(
                    "a[href*='/opportunity/'], a[href*='/job/'], a[href*='/listing/']"
                )
                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href:
                        url = href if href.startswith("http") else f"https://unstop.com{href}"

                jobs.append(RawJobData(
                    title=title,
                    company_name=company,
                    description=description,
                    location=location,
                    url=url,
                    source_job_id=self._extract_opportunity_id(card),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency or "INR",
                    salary_period=period or "monthly",
                    posted_at=posted_at,
                    job_type=opportunity_type,
                    remote="remote" in (location or "").lower() or "work from home" in (location or "").lower(),
                    apply_url=url,
                    skills=skills,
                    raw={
                        "source": "unstop", "query": query,
                        "opportunity_type": opp_type,
                    },
                ))
            except Exception:
                logger.exception("Failed to parse Unstop card")

        return jobs

    def _extract_opportunity_id(self, card) -> str | None:
        opp_id = card.get("data-id") or card.get("id")
        if opp_id:
            return str(opp_id)
        url_el = card.select_one("a[href*='/opportunity/']")
        if url_el:
            href = url_el.get("href", "")
            match = re.search(r"/opportunity/(\w+)", href)
            if match:
                return match.group(1)
        return None

    def _parse_stipend(self, text: str) -> tuple:
        text = text.replace(",", "").replace("₹", "").replace("Rs ", "")
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        currency = "INR"
        period = "monthly"

        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1]), currency, period
        if len(numbers) == 1:
            val = float(numbers[0])
            if "lac" in text.lower() or "lakh" in text.lower():
                val *= 100000
                period = "yearly"
            elif "k" in text.lower():
                val *= 1000
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
