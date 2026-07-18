import logging

from app.services.providers.base import BaseProvider, RawJobData

logger = logging.getLogger(__name__)


class CareerPagesProvider(BaseProvider):
    """Generic provider for company career pages.

    Configure per-company URLs and selectors via extra_params.
    Falls back to common patterns for Greenhouse, Lever, Ashby,
    or attempts HTML scraping with configurable CSS selectors.
    """

    @property
    def name(self) -> str:
        return "career_pages"

    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search configured company career pages."""
        companies = kwargs.get("companies") or self.settings.extra_params.get(
            "companies", ""
        ).split(",")
        companies = [c.strip() for c in companies if c.strip()]

        if not companies:
            logger.info("No career page companies configured")
            return []

        all_jobs: list[RawJobData] = []
        for company in companies:
            try:
                jobs = await self._scrape_company(company, query, kwargs)
                all_jobs.extend(jobs)
            except Exception:
                logger.exception("Failed to scrape career page for '%s'", company)

        return all_jobs

    async def _scrape_company(self, company: str, query: str, kwargs: dict) -> list[RawJobData]:
        """Scrape a single company's career page."""
        url = kwargs.get(f"{company}_url") or self._guess_career_page_url(company)
        if not url:
            logger.warning("No URL for company '%s'", company)
            return []

        try:
            html = await self._get_html(url)
        except Exception:
            logger.debug("Failed to fetch career page for '%s': %s", company, url)
            return []

        selectors = kwargs.get("selectors", {})

        return self._parse_listing_page(html, company, url, query, selectors)

    def _guess_career_page_url(self, company: str) -> str:
        """Guess the career page URL for a company."""
        company_clean = company.lower().replace(" ", "").replace(".", "")
        candidates = [
            f"https://{company_clean}.com/careers",
            f"https://{company_clean}.com/jobs",
            f"https://careers.{company_clean}.com",
            f"https://www.{company_clean}.com/careers",
        ]
        return candidates[0]

    def _parse_listing_page(
        self,
        html: str,
        company: str,
        base_url: str,
        query: str,
        selectors: dict[str, str],
    ) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        jobs: list[RawJobData] = []
        query_lower = query.lower()

        job_link_selector = selectors.get(
            "job_link",
            "a[href*='careers'], a[href*='jobs'], a[href*='position'], a[href*='job']",
        )
        title_selector = selectors.get("title", "h2, h3, .job-title, .posting-title")
        location_selector = selectors.get("location", ".location, .job-location, .posting-location")

        links = soup.select(job_link_selector)
        if not links:
            links = soup.find_all("a", href=True)

        seen_urls: set[str] = set()
        for link in links:
            href = link.get("href", "")
            if not href or href in seen_urls:
                continue
            if href.startswith("#") or href.startswith("javascript"):
                continue

            full_url = href if href.startswith("http") else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
            seen_urls.add(full_url)

            title = "Unknown"
            title_el = link.select_one(title_selector) if selectors.get("title") else link
            if title_el:
                title = title_el.get_text(strip=True)
            elif link.get_text(strip=True):
                title = link.get_text(strip=True).split("\n")[0].strip()

            if query and query_lower not in title.lower():
                continue

            location_el = link.select_one(location_selector) if selectors.get("location") else None
            location = location_el.get_text(strip=True) if location_el else None

            jobs.append(RawJobData(
                title=title,
                company_name=company.title(),
                location=location,
                url=full_url,
                remote="remote" in (location or "").lower(),
                raw={"source": "career_pages", "company": company, "query": query},
            ))

        return jobs
