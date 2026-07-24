from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig
from app.intelligence.exceptions import OptimizationDataError

logger = structlog.get_logger(__name__)


class OptimizationEngine:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._logger = logger.bind(engine="optimization")

    async def optimize(self, context: dict[str, Any]) -> dict[str, Any]:
        history = context.get("history", [])
        if len(history) < self._config.min_data_points_for_optimization:
            raise OptimizationDataError(
                f"Insufficient history: need at least {self._config.min_data_points_for_optimization} data points"
            )

        results = {}
        if context.get("optimize_matching"):
            preferences = context.get("preferences", {})
            results["matching"] = await self.optimize_matching(history, preferences)
        if context.get("optimize_prompts"):
            results["prompts"] = await self.optimize_prompts(history)
        if context.get("optimize_providers"):
            results["providers"] = await self.optimize_providers(history)
        if context.get("optimize_strategies"):
            results["strategies"] = await self.optimize_strategies(history)

        return results

    async def optimize_matching(self, history: list[dict[str, Any]], preferences: dict[str, Any]) -> dict[str, Any]:
        if not history:
            raise OptimizationDataError("No history available for match optimization")

        successful = [h for h in history if h.get("status") == "success" or h.get("success") is True]
        if not successful:
            return {
                "recommendations": ["Gather more successful application data before optimizing matches"],
                "improvements": {},
                "confidence": 0.0,
                "details": {"total_history": len(history), "successful": 0},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        top_industries: dict[str, int] = {}
        top_companies: dict[str, int] = {}
        top_locations: dict[str, int] = {}
        skill_demand: dict[str, int] = {}

        for entry in successful:
            industry = entry.get("industry") or "unknown"
            top_industries[industry] = top_industries.get(industry, 0) + 1
            company = entry.get("company") or entry.get("company_name") or "unknown"
            top_companies[company] = top_companies.get(company, 0) + 1
            location = entry.get("location") or entry.get("city") or "unknown"
            top_locations[location] = top_locations.get(location, 0) + 1
            for skill in entry.get("skills") or entry.get("required_skills") or []:
                skill_demand[skill] = skill_demand.get(skill, 0) + 1

        sorted_industries = sorted(top_industries.items(), key=lambda x: x[1], reverse=True)
        sorted_companies = sorted(top_companies.items(), key=lambda x: x[1], reverse=True)
        sorted_skills = sorted(skill_demand.items(), key=lambda x: x[1], reverse=True) if skill_demand else []

        recommendations = []
        if sorted_industries:
            recommendations.append(f"Focus on {sorted_industries[0][0]} industry")
        if sorted_companies:
            recommendations.append(f"Prioritize applications to {sorted_companies[0][0]}")
        if sorted_skills:
            top_skills = [s[0] for s in sorted_skills[:5]]
            recommendations.append(f"Highlight skills: {', '.join(top_skills)}")
        if sorted_locations := sorted(top_locations.items(), key=lambda x: x[1], reverse=True):
            recommendations.append(f"Target locations: {sorted_locations[0][0]}")

        return {
            "recommendations": recommendations,
            "improvements": {
                "industry_focus": len(sorted_industries),
                "company_focus": len(sorted_companies),
                "skill_coverage": len(sorted_skills),
            },
            "confidence": round(len(successful) / len(history), 4) if history else 0.0,
            "details": {
                "total_history": len(history),
                "successful": len(successful),
                "top_industries": [{"industry": k, "count": v} for k, v in sorted_industries[:5]],
                "top_companies": [{"company": k, "count": v} for k, v in sorted_companies[:5]],
                "top_skills": [{"skill": k, "demand": v} for k, v in sorted_skills[:10]],
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    async def optimize_prompts(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not history:
            raise OptimizationDataError("No prompt history available")

        templates: dict[str, list[dict[str, Any]]] = {}
        for entry in history:
            template = entry.get("template") or entry.get("prompt_template") or "unknown"
            templates.setdefault(template, []).append(entry)

        results = []
        for template_name, entries in templates.items():
            total = len(entries)
            successful = sum(1 for e in entries if e.get("status") == "success" or e.get("success") is True)
            qualities = [e.get("quality", 0) for e in entries if e.get("quality") is not None]
            latencies = [e.get("latency", 0) for e in entries if e.get("latency") is not None]
            costs = [e.get("cost", 0) for e in entries if e.get("cost") is not None]
            tokens = [e.get("tokens", 0) for e in entries if e.get("tokens") is not None]

            success_rate = successful / total if total > 0 else 0.0
            avg_quality = mean(qualities) if qualities else 0.0
            avg_latency = mean(latencies) if latencies else 0.0
            avg_cost = mean(costs) if costs else 0.0
            avg_tokens = int(mean(tokens)) if tokens else 0

            score = (
                success_rate * 0.4
                + avg_quality * 0.3
                + (1.0 - min(avg_latency / 10000, 1.0)) * 0.15
                + (1.0 - min(avg_cost / 0.1, 1.0)) * 0.15
            )

            results.append(
                {
                    "template": template_name,
                    "score": round(score, 4),
                    "success_rate": round(success_rate, 4),
                    "avg_quality": round(avg_quality, 4),
                    "avg_latency": round(avg_latency, 2),
                    "avg_cost": round(avg_cost, 6),
                    "avg_tokens": avg_tokens,
                    "total_uses": total,
                }
            )

        results.sort(key=lambda r: r["score"], reverse=True)

        for i, result in enumerate(results):
            result["rank"] = i + 1
            if i > 0:
                prev = results[i - 1]
                if prev["score"] > 0:
                    result["improvement_needed"] = round((prev["score"] - result["score"]) / prev["score"] * 100, 2)

        return results

    async def optimize_providers(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not history:
            raise OptimizationDataError("No provider history available")

        providers: dict[str, list[dict[str, Any]]] = {}
        for entry in history:
            provider = entry.get("provider") or entry.get("provider_name") or "unknown"
            providers.setdefault(provider, []).append(entry)

        results = []
        for provider_name, entries in providers.items():
            total = len(entries)
            successful = sum(1 for e in entries if e.get("status") == "success" or e.get("success") is True)
            errors = sum(1 for e in entries if e.get("error") or e.get("status") == "error")
            latencies = [e.get("latency", 0) for e in entries if e.get("latency") is not None]
            costs = [e.get("cost", 0) for e in entries if e.get("cost") is not None]

            success_rate = successful / total if total > 0 else 0.0
            error_rate = errors / total if total > 0 else 0.0
            avg_latency = mean(latencies) if latencies else float("inf")
            avg_cost = mean(costs) if costs else 0.0
            availability = 1.0 - error_rate

            latency_score = 1.0 - min(avg_latency / 10000, 1.0) if avg_latency != float("inf") else 0.0
            cost_score = 1.0 - min(avg_cost / 0.1, 1.0)

            overall = success_rate * 0.35 + availability * 0.25 + latency_score * 0.20 + cost_score * 0.20

            results.append(
                {
                    "provider": provider_name,
                    "overall_score": round(overall, 4),
                    "success_rate": round(success_rate, 4),
                    "availability": round(availability, 4),
                    "error_rate": round(error_rate, 4),
                    "avg_latency": round(avg_latency, 2),
                    "avg_cost": round(avg_cost, 6),
                    "total_uses": total,
                }
            )

        results.sort(key=lambda r: r["overall_score"], reverse=True)

        for i, result in enumerate(results):
            result["rank"] = i + 1
            result["recommended"] = i == 0

        return results

    async def optimize_strategies(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        if not history:
            raise OptimizationDataError("No strategy history available")

        strategies: dict[str, list[bool]] = {}
        for entry in history:
            strategy = entry.get("strategy") or entry.get("strategy_type") or "default"
            success = entry.get("status") == "success" or entry.get("success") is True
            strategies.setdefault(strategy, []).append(success)

        scored = []
        for strategy_name, outcomes in strategies.items():
            total = len(outcomes)
            successful = sum(1 for s in outcomes if s)
            rate = successful / total if total > 0 else 0.0
            scored.append(
                {
                    "strategy": strategy_name,
                    "success_rate": round(rate, 4),
                    "successful": successful,
                    "total": total,
                }
            )

        scored.sort(key=lambda r: (r["success_rate"], r["total"]), reverse=True)
        best = scored[0] if scored else None

        return {
            "recommendations": [f"Use '{best['strategy']}' strategy" for best in [scored[0]]] if scored else [],
            "improvements": {s["strategy"]: s["success_rate"] for s in scored},
            "confidence": round(best["success_rate"], 4) if best else 0.0,
            "details": {"scored_strategies": scored},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
