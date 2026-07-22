from __future__ import annotations

from datetime import datetime

from app.application_intelligence.config import ApplicationIntelligenceConfig
from app.application_intelligence.schemas import (
    CompanyIntelligence,
    CompanyType,
    HiringPriority,
)


class CompanyAnalyzer:
    def __init__(self, config: ApplicationIntelligenceConfig) -> None:
        self._config = config

    def analyze(self, job) -> CompanyIntelligence:
        result = CompanyIntelligence()
        if not job:
            return result

        company = getattr(job, "company", None)
        description = (getattr(job, "description", None) or "").lower()
        title = (getattr(job, "title", None) or "").lower()
        full_text = f"{description} {title}"

        result.company_size = self._extract_company_size(company)
        result.industry_classification = self._extract_industry(company)
        result.company_type = self._classify_company_type(company, full_text)
        result.is_startup = result.company_type == CompanyType.STARTUP
        result.summary = self._generate_summary(result, job)
        result.remote_policy = self._extract_remote_policy(job)
        result.hiring_priority = self._infer_hiring_priority(job)
        return result

    def _extract_company_size(self, company) -> str | None:
        if not company:
            return None
        size = getattr(company, "size", None)
        if size:
            return str(size)
        return None

    def _extract_industry(self, company) -> str | None:
        if not company:
            return None
        return getattr(company, "industry", None)

    def _classify_company_type(self, company, full_text: str) -> CompanyType:
        company_name = ""
        company_desc = ""
        if company:
            company_name = (getattr(company, "name", None) or "").lower()
            company_desc = (getattr(company, "description", None) or "").lower()

        search_text = f"{company_name} {company_desc} {full_text}"

        if any(kw in search_text for kw in self._config.startup_keywords):
            return CompanyType.STARTUP

        if any(kw in search_text for kw in self._config.enterprise_keywords):
            return CompanyType.ENTERPRISE

        consulting_words = ("consulting", "consultancy", "advisory", "mckinsey", "bain", "boston consulting")
        if any(kw in search_text for kw in consulting_words):
            return CompanyType.CONSULTING

        gov_words = ("government", "public sector", "federal", "state agency", "municipal")
        if any(kw in search_text for kw in gov_words):
            return CompanyType.GOVERNMENT

        nonprofit_words = ("nonprofit", "non-profit", "ngo", "foundation", "charity")
        if any(kw in search_text for kw in nonprofit_words):
            return CompanyType.NON_PROFIT

        return CompanyType.UNKNOWN

    def _generate_summary(self, result: CompanyIntelligence, job) -> str | None:
        company = getattr(job, "company", None)
        if not company:
            return None
        name = getattr(company, "name", None)
        if not name:
            return None
        parts = [name]
        if result.industry_classification:
            parts.append(f"({result.industry_classification})")
        return " ".join(parts) if parts else None

    def _extract_remote_policy(self, job) -> str | None:
        loc = getattr(job, "location", None) if job else None
        if loc:
            rt = getattr(loc, "remote_type", None)
            if rt:
                return str(rt)

        description = (getattr(job, "description", None) or "").lower()
        if "remote" in description:
            if "fully remote" in description or "100% remote" in description:
                return "remote"
            if "hybrid" in description:
                return "hybrid"
            if "on-site" in description or "on site" in description:
                return "on_site"
            return "remote"
        return None

    def _infer_hiring_priority(self, job) -> HiringPriority:
        if not job:
            return HiringPriority.UNKNOWN

        description = (getattr(job, "description", None) or "").lower()
        urgency_signals = 0

        urgency_phrases = (
            "urgent", "immediate", "asap", "quickly", "fast", "growing rapidly",
            "high priority", "critical role", "key hire",
        )
        for phrase in urgency_phrases:
            if phrase in description:
                urgency_signals += 1

        recent = getattr(job, "posted_date", None)
        if recent is not None:
            try:
                delta = datetime.utcnow() - recent
                if hasattr(delta, "days") and delta.days is not None and delta.days < 7:
                    urgency_signals += 1
            except TypeError:
                pass

        if urgency_signals >= 3:
            return HiringPriority.HIGH
        if urgency_signals >= 1:
            return HiringPriority.MEDIUM
        return HiringPriority.LOW
