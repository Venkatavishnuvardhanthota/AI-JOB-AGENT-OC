import logging

from app.schemas.matching import CompanyScore

logger = logging.getLogger(__name__)

REPUTABLE_COMPANIES: set[str] = set()
BLACKLISTED_INDUSTRIES: set[str] = set()

INDUSTRY_KEYWORDS: dict[str, set[str]] = {
    "technology": {"tech", "software", "saas", "cloud", "it", "computer", "internet", "digital"},
    "finance": {"bank", "financial", "finance", "insurance", "investment", "hedge fund", "vc"},
    "healthcare": {"health", "medical", "pharma", "biotech", "healthcare", "clinical"},
    "consulting": {"consulting", "consultancy", "advisory"},
    "ecommerce": {"ecommerce", "e-commerce", "retail", "marketplace"},
}


class CompanyAnalyzer:
    def analyze(
        self,
        company_name: str,
        blacklisted_companies: list[str],
        user_experience_companies: list[str],
    ) -> CompanyScore:
        name_lower = (company_name or "").lower().strip()
        is_blacklisted = any(
            bc.lower().strip() == name_lower for bc in blacklisted_companies
        )
        has_connections = any(
            exp_co.lower().strip() == name_lower
            for exp_co in user_experience_companies
        )
        score = 1.0
        if is_blacklisted:
            score = 0.0
        elif has_connections:
            score = 0.9
        else:
            score = 0.5
        return CompanyScore(
            company_name=company_name or "",
            is_blacklisted=is_blacklisted,
            has_connections=has_connections,
            score=round(score, 4),
        )
