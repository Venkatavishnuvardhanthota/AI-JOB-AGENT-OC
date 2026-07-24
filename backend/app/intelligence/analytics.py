from __future__ import annotations

from statistics import mean, median
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig
from app.intelligence.exceptions import AnalyticsDataError

logger = structlog.get_logger(__name__)


class AnalyticsEngine:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._logger = logger.bind(engine="analytics")

    async def analyze(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        if not data:
            raise AnalyticsDataError("No data provided for analysis")

        return {
            "application_success_rate": await self.application_success_rate(data),
            "provider_success_rate": await self.provider_success_rate(data),
            "resume_effectiveness": await self.resume_effectiveness(data),
            "cover_letter_effectiveness": await self.cover_letter_effectiveness(data),
            "job_source_effectiveness": await self.job_source_effectiveness(data),
            "salary_trends": await self.salary_trends(data),
            "location_trends": await self.location_trends(data),
            "industry_trends": await self.industry_trends(data),
            "company_trends": await self.company_trends(data),
            "response_time": await self.response_time(data),
            "acceptance_rate": await self.acceptance_rate(data),
            "rejection_rate": await self.rejection_rate(data),
            "total_applications": len(data),
            "sample_size": len(data),
        }

    async def application_success_rate(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(data)
        if total == 0:
            raise AnalyticsDataError("No application data available")

        successful = sum(1 for d in data if d.get("status") == "success" or d.get("success") is True)
        rate = successful / total if total > 0 else 0.0

        return {
            "rate": round(rate, 4),
            "successful": successful,
            "total": total,
            "percentage": round(rate * 100, 2),
        }

    async def provider_success_rate(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        providers: dict[str, list[bool]] = {}
        for d in data:
            provider = d.get("provider") or d.get("provider_name") or "unknown"
            success = d.get("status") == "success" or d.get("success") is True
            providers.setdefault(provider, []).append(success)

        results = []
        for provider, outcomes in providers.items():
            total = len(outcomes)
            successful = sum(1 for s in outcomes if s)
            rate = successful / total if total > 0 else 0.0
            results.append(
                {
                    "provider": provider,
                    "rate": round(rate, 4),
                    "successful": successful,
                    "total": total,
                    "percentage": round(rate * 100, 2),
                }
            )

        return sorted(results, key=lambda r: r["rate"], reverse=True)

    async def resume_effectiveness(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        resumes: dict[str, list[bool]] = {}
        for d in data:
            resume = d.get("resume_id") or d.get("resume") or "unknown"
            success = d.get("status") == "success" or d.get("success") is True
            resumes.setdefault(resume, []).append(success)

        if not resumes:
            raise AnalyticsDataError("No resume data available")

        results = []
        for resume_id, outcomes in resumes.items():
            total = len(outcomes)
            successful = sum(1 for s in outcomes if s)
            rate = successful / total if total > 0 else 0.0
            results.append({"resume_id": resume_id, "rate": round(rate, 4), "successful": successful, "total": total})

        results.sort(key=lambda r: r["rate"], reverse=True)
        best = results[0] if results else None
        avg_rate = mean([r["rate"] for r in results]) if results else 0.0

        return {
            "best_resume": best,
            "all_resumes": results,
            "average_rate": round(avg_rate, 4),
            "total_resumes": len(results),
        }

    async def cover_letter_effectiveness(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        cover_letters: dict[str, list[bool]] = {}
        for d in data:
            cl = d.get("cover_letter_id") or d.get("cover_letter") or "none"
            success = d.get("status") == "success" or d.get("success") is True
            cover_letters.setdefault(cl, []).append(success)

        if not cover_letters:
            return {
                "best_cover_letter": None,
                "all_cover_letters": [],
                "average_rate": 0.0,
                "total_cover_letters": 0,
            }

        results = []
        for cl_id, outcomes in cover_letters.items():
            total = len(outcomes)
            successful = sum(1 for s in outcomes if s)
            rate = successful / total if total > 0 else 0.0
            results.append({"cover_letter_id": cl_id, "rate": round(rate, 4), "successful": successful, "total": total})

        results.sort(key=lambda r: r["rate"], reverse=True)
        best = results[0] if results else None
        avg_rate = mean([r["rate"] for r in results]) if results else 0.0

        return {
            "best_cover_letter": best,
            "all_cover_letters": results,
            "average_rate": round(avg_rate, 4),
            "total_cover_letters": len(results),
        }

    async def job_source_effectiveness(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        sources: dict[str, list[bool]] = {}
        for d in data:
            source = d.get("source") or d.get("job_source") or d.get("provider") or "unknown"
            success = d.get("status") == "success" or d.get("success") is True
            sources.setdefault(source, []).append(success)

        results = []
        for source, outcomes in sources.items():
            total = len(outcomes)
            successful = sum(1 for s in outcomes if s)
            rate = successful / total if total > 0 else 0.0
            results.append(
                {
                    "source": source,
                    "rate": round(rate, 4),
                    "successful": successful,
                    "total": total,
                    "percentage": round(rate * 100, 2),
                }
            )

        return sorted(results, key=lambda r: r["rate"], reverse=True)

    async def salary_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        salaries = [d.get("salary") for d in data if d.get("salary") is not None]
        if not salaries:
            return []

        return [
            {"metric": "average", "value": round(mean(salaries), 2)},
            {"metric": "median", "value": round(median(salaries), 2)},
            {"metric": "min", "value": min(salaries)},
            {"metric": "max", "value": max(salaries)},
            {"metric": "total", "value": len(salaries)},
        ]

    async def location_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        locations: dict[str, int] = {}
        for d in data:
            loc = d.get("location") or d.get("city") or "unknown"
            locations[loc] = locations.get(loc, 0) + 1

        total = sum(locations.values())
        results = [
            {"location": loc, "count": count, "percentage": round(count / total * 100, 2) if total > 0 else 0.0}
            for loc, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)
        ]
        return results

    async def industry_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        industries: dict[str, int] = {}
        for d in data:
            industry = d.get("industry") or "unknown"
            industries[industry] = industries.get(industry, 0) + 1

        total = sum(industries.values())
        results = [
            {"industry": ind, "count": count, "percentage": round(count / total * 100, 2) if total > 0 else 0.0}
            for ind, count in sorted(industries.items(), key=lambda x: x[1], reverse=True)
        ]
        return results

    async def company_trends(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        companies: dict[str, int] = {}
        for d in data:
            company = d.get("company") or d.get("company_name") or "unknown"
            companies[company] = companies.get(company, 0) + 1

        total = sum(companies.values())
        results = [
            {"company": comp, "count": count, "percentage": round(count / total * 100, 2) if total > 0 else 0.0}
            for comp, count in sorted(companies.items(), key=lambda x: x[1], reverse=True)
        ]
        return results

    async def response_time(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        times = [
            d.get("response_time_days") or d.get("response_time")
            for d in data
            if d.get("response_time_days") is not None or d.get("response_time") is not None
        ]
        if not times:
            return {"average_days": None, "median_days": None, "min_days": None, "max_days": None, "total": 0}

        return {
            "average_days": round(mean(times), 2),
            "median_days": round(median(times), 2),
            "min_days": min(times),
            "max_days": max(times),
            "total": len(times),
        }

    async def acceptance_rate(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(data)
        if total == 0:
            raise AnalyticsDataError("No application data available")

        accepted = sum(1 for d in data if d.get("status") in ("accepted", "offer", "hired"))
        rate = accepted / total if total > 0 else 0.0

        return {
            "rate": round(rate, 4),
            "accepted": accepted,
            "total": total,
            "percentage": round(rate * 100, 2),
        }

    async def rejection_rate(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(data)
        if total == 0:
            raise AnalyticsDataError("No application data available")

        rejected = sum(1 for d in data if d.get("status") in ("rejected", "declined"))
        rate = rejected / total if total > 0 else 0.0

        return {
            "rate": round(rate, 4),
            "rejected": rejected,
            "total": total,
            "percentage": round(rate * 100, 2),
        }
