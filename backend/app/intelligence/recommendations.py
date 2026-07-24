from __future__ import annotations

from statistics import mean
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig
from app.intelligence.exceptions import RecommendationDataError

logger = structlog.get_logger(__name__)


class RecommendationEngine:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._logger = logger.bind(engine="recommendations")

    async def recommend(self, context: dict[str, Any]) -> dict[str, Any]:
        history = context.get("history", [])
        if len(history) < self._config.min_data_points_for_recommendations:
            raise RecommendationDataError(
                f"Insufficient history: need at least {self._config.min_data_points_for_recommendations} data points"
            )

        results = {}
        if context.get("want_resume"):
            results["best_resume"] = await self.best_resume(history)
        if context.get("want_cover_letter"):
            results["best_cover_letter"] = await self.best_cover_letter(history)
        if context.get("want_provider"):
            results["best_provider"] = await self.best_provider(history)
        if context.get("want_strategy"):
            results["best_strategy"] = await self.best_strategy(history)
        if context.get("want_timing"):
            results["best_timing"] = await self.best_timing(history)
        if context.get("want_ai_model"):
            results["best_ai_model"] = await self.best_ai_model(history)
        if context.get("want_prompt_template"):
            results["best_prompt_template"] = await self.best_prompt_template(history)
        if context.get("want_retry_strategy"):
            results["best_retry_strategy"] = await self.best_retry_strategy(history)

        return results

    async def best_resume(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        resumes: dict[str, list[bool]] = {}
        for entry in history:
            resume = entry.get("resume_id") or entry.get("resume") or "unknown"
            success = entry.get("status") == "success" or entry.get("success") is True
            resumes.setdefault(resume, []).append(success)

        if not resumes:
            raise RecommendationDataError("No resume history available")

        scored = [
            {"id": rid, "rate": sum(1 for s in outcomes if s) / len(outcomes), "total": len(outcomes)}
            for rid, outcomes in resumes.items()
        ]
        scored.sort(key=lambda r: r["rate"], reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"Resume {best['id']} has the highest success rate ({best['rate']:.1%}) "
            f"based on {best['total']} applications",
            "supporting_data": {"scored_resumes": scored},
        }

    async def best_cover_letter(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        cover_letters: dict[str, list[bool]] = {}
        for entry in history:
            cl = entry.get("cover_letter_id") or entry.get("cover_letter") or "none"
            success = entry.get("status") == "success" or entry.get("success") is True
            cover_letters.setdefault(cl, []).append(success)

        if not cover_letters or all(k == "none" for k in cover_letters):
            raise RecommendationDataError("No cover letter history available")

        scored = [
            {"id": cid, "rate": sum(1 for s in outcomes if s) / len(outcomes), "total": len(outcomes)}
            for cid, outcomes in cover_letters.items()
            if cid != "none"
        ]
        if not scored:
            raise RecommendationDataError("No cover letter history available")

        scored.sort(key=lambda r: r["rate"], reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"Cover letter {best['id']} has the highest success rate ({best['rate']:.1%}) "
            f"based on {best['total']} applications",
            "supporting_data": {"scored_cover_letters": scored},
        }

    async def best_provider(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        providers: dict[str, list[bool]] = {}
        for entry in history:
            provider = entry.get("provider") or entry.get("provider_name") or "unknown"
            success = entry.get("status") == "success" or entry.get("success") is True
            providers.setdefault(provider, []).append(success)

        if not providers:
            raise RecommendationDataError("No provider history available")

        scored = [
            {
                "id": pid,
                "rate": sum(1 for s in outcomes if s) / len(outcomes),
                "total": len(outcomes),
                "success_count": sum(1 for s in outcomes if s),
            }
            for pid, outcomes in providers.items()
        ]
        scored.sort(key=lambda r: (r["rate"], r["total"]), reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"Provider {best['id']} has the highest success rate ({best['rate']:.1%}) "
            f"with {best['success_count']} successes out of {best['total']} attempts",
            "supporting_data": {"scored_providers": scored},
        }

    async def best_strategy(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        strategies: dict[str, list[bool]] = {}
        for entry in history:
            strategy = entry.get("strategy") or entry.get("strategy_type") or "default"
            success = entry.get("status") == "success" or entry.get("success") is True
            strategies.setdefault(strategy, []).append(success)

        if not strategies:
            raise RecommendationDataError("No strategy history available")

        scored = [
            {
                "id": sid,
                "rate": sum(1 for s in outcomes if s) / len(outcomes),
                "total": len(outcomes),
            }
            for sid, outcomes in strategies.items()
        ]
        scored.sort(key=lambda r: (r["rate"], r["total"]), reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"Strategy '{best['id']}' has the highest success rate ({best['rate']:.1%}) "
            f"based on {best['total']} attempts",
            "supporting_data": {"scored_strategies": scored},
        }

    async def best_timing(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        time_slots: dict[str, list[bool]] = {}
        for entry in history:
            hour = entry.get("hour") or entry.get("submission_hour")
            if hour is None:
                continue
            slot = f"{int(hour):02d}:00"
            success = entry.get("status") == "success" or entry.get("success") is True
            time_slots.setdefault(slot, []).append(success)

        if not time_slots:
            raise RecommendationDataError("No timing history available")

        scored = [
            {
                "id": slot,
                "rate": sum(1 for s in outcomes if s) / len(outcomes),
                "total": len(outcomes),
            }
            for slot, outcomes in time_slots.items()
        ]
        scored.sort(key=lambda r: (r["rate"], r["total"]), reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"Submissions around {best['id']} have the highest success rate ({best['rate']:.1%})",
            "supporting_data": {"scored_time_slots": scored},
        }

    async def best_ai_model(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        models: dict[str, list[dict[str, Any]]] = {}
        for entry in history:
            model = entry.get("model") or entry.get("ai_model") or "unknown"
            models.setdefault(model, []).append(entry)

        if not models:
            raise RecommendationDataError("No AI model history available")

        scored = []
        for model_id, entries in models.items():
            total = len(entries)
            successful = sum(1 for e in entries if e.get("status") == "success" or e.get("success") is True)
            qualities = [e.get("quality", 0) for e in entries if e.get("quality") is not None]
            avg_quality = mean(qualities) if qualities else 0.0
            rate = successful / total if total > 0 else 0.0
            scored.append(
                {
                    "id": model_id,
                    "rate": rate,
                    "avg_quality": round(avg_quality, 4),
                    "total": total,
                }
            )

        scored.sort(key=lambda r: (r["rate"], r["avg_quality"]), reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"AI model {best['id']} has the best performance with {best['rate']:.1%} success rate "
            f"and average quality {best['avg_quality']:.2f}",
            "supporting_data": {"scored_models": scored},
        }

    async def best_prompt_template(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        templates: dict[str, list[dict[str, Any]]] = {}
        for entry in history:
            template = entry.get("template") or entry.get("prompt_template") or "unknown"
            templates.setdefault(template, []).append(entry)

        if not templates:
            raise RecommendationDataError("No prompt template history available")

        scored = []
        for template_id, entries in templates.items():
            total = len(entries)
            successful = sum(1 for e in entries if e.get("status") == "success" or e.get("success") is True)
            costs = [e.get("cost", 0) for e in entries if e.get("cost") is not None]
            latencies = [e.get("latency", 0) for e in entries if e.get("latency") is not None]
            avg_cost = mean(costs) if costs else 0.0
            avg_latency = mean(latencies) if latencies else 0.0
            rate = successful / total if total > 0 else 0.0
            scored.append(
                {
                    "id": template_id,
                    "rate": rate,
                    "avg_cost": round(avg_cost, 4),
                    "avg_latency": round(avg_latency, 2),
                    "total": total,
                }
            )

        scored.sort(key=lambda r: (r["rate"], -r["avg_cost"], -r["avg_latency"]), reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"Prompt template '{best['id']}' has the best balance of success rate ({best['rate']:.1%}), "
            f"cost ({best['avg_cost']:.4f}), and latency ({best['avg_latency']:.1f}ms)",
            "supporting_data": {"scored_templates": scored},
        }

    async def best_retry_strategy(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        strategies: dict[str, list[dict[str, Any]]] = {}
        for entry in history:
            strategy = entry.get("retry_strategy") or entry.get("strategy") or "default"
            strategies.setdefault(strategy, []).append(entry)

        if not strategies:
            raise RecommendationDataError("No retry strategy history available")

        scored = []
        for strategy_id, entries in strategies.items():
            total = len(entries)
            successful = sum(1 for e in entries if e.get("status") == "success" or e.get("success") is True)
            rate = successful / total if total > 0 else 0.0
            scored.append({"id": strategy_id, "rate": rate, "total": total})

        scored.sort(key=lambda r: (r["rate"], r["total"]), reverse=True)
        best = scored[0]

        return {
            "recommended_value": best["id"],
            "confidence": round(best["rate"], 4),
            "alternatives": [s["id"] for s in scored[1:]],
            "reasoning": f"Retry strategy '{best['id']}' has the highest success rate ({best['rate']:.1%}) "
            f"based on {best['total']} attempts",
            "supporting_data": {"scored_strategies": scored},
        }
