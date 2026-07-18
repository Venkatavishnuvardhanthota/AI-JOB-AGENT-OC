import logging
import re
from datetime import datetime

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class InternshalaProvider(BaseProvider):
    """Provider for Internshala internships and jobs via scraping."""

    @property
    def name(self) -> str:
        return "internshala"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search Internshala for internships/jobs matching the query."""
        params: dict[str, str] = {"q": query}
        if kwargs.get("location"):
            params["city"] = kwargs["location"]
        if kwargs.get("remote_only"):
            params["work_from_home"] = "true"

        category = kwargs.get("category", "internships")
        if category not in ("internships", "jobs"):
            category = "internships"

        try:
            html = await self._get_html(
                f"{self.settings.base_url}/{category}",
                params=params,
            )
        except Exception:
            logger.warning("Internshala search failed, returning empty results")
            return []

        return self._parse_search_results(html, query, category, remote_only=kwargs.get("remote_only", False))

    def _parse_search_results(
        self, html: str, query: str, category: str, remote_only: bool = False,
    ) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []

        for card in soup.select(
            ".internship_meta, .individual_internship, .job-card, .internship-list-item, "
            "[data-test='internship-card'], .card"
        ):
            try:
                title_el = card.select_one(
                    ".heading_4_5 a, .job-title a, h3 a, .title a, [class*='title'] a"
                )
                company_el = card.select_one(
                    ".company-name, .company, .heading_6, .link_display_like_button, "
                    "[class*='company']"
                )
                location_el = card.select_one(
                    ".location, .loc, .locations, [class*='location'], .job-location"
                )
                stipend_el = card.select_one(
                    ".stipend, .salary, .money, [class*='stipend'], [class*='salary']"
                )
                skill_els = card.select(
                    ".skill, .tag, .round_tabs, [class*='skill'], [class*='tag']"
                )
                date_el = card.select_one(
                    ".date, .posted, .time, [class*='date'], [class*='posted']"
                )
                desc_el = card.select_one(
                    ".description, .desc, .internship_description, .text-container"
                )
                duration_el = card.select_one(
                    ".duration, [class*='duration'], .internship_length"
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
                duration = duration_el.get_text(strip=True) if duration_el else None

                url_el = title_el or card.select_one("a[href*='/internship/'], a[href*='/job/']")
                url = None
                if url_el:
                    href = url_el.get("href", "")
                    if href:
                        url = href if href.startswith("http") else f"https://internshala.com{href}"

                remote_val = False
                if location and ("work from home" in location.lower() or "remote" in location.lower()):
                    remote_val = True
                if remote_only:
                    remote_val = True

                job_type = category.rstrip("s")
                if duration and "intern" in category:
                    job_type = f"{job_type}/{duration}" if duration else job_type

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
                    salary_period=period or "monthly",
                    posted_at=posted_at,
                    job_type=job_type,
                    remote=remote_val,
                    apply_url=url,
                    skills=skills,
                    raw={
                        "source": "internshala", "query": query,
                        "category": category, "duration": duration,
                    },
                ))
            except Exception:
                logger.exception("Failed to parse Internshala card")

        return jobs

    def _extract_job_id(self, card) -> str | None:
        job_id = card.get("data-internship-id") or card.get("data-id") or card.get("id")
        if job_id:
            return str(job_id)
        url_el = card.select_one("a[href*='/internship/'], a[href*='/job/']")
        if url_el:
            href = url_el.get("href", "")
            match = re.search(r"/(?:internship|job)/(?:[a-z-]+-)?(\d+)", href)
            if match:
                return match.group(1)
        return None

    def _parse_stipend(self, text: str) -> tuple:
        text = text.replace(",", "").replace("₹", "").replace("Rs ", "").replace("/month", "")
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        currency = "INR"
        period = "monthly"

        if len(numbers) >= 2:
            return float(numbers[0]), float(numbers[1]), currency, period
        if len(numbers) == 1:
            if "lac" in text.lower() or "lakh" in text.lower():
                val = float(numbers[0]) * 100000
                period = "yearly"
            else:
                val = float(numbers[0])
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
