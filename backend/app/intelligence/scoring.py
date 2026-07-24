from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig
from app.intelligence.exceptions import ScoringError

logger = structlog.get_logger(__name__)


class ScoringEngine:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._logger = logger.bind(engine="scoring")

    async def score(self, model: str, data: dict[str, Any]) -> dict[str, Any]:
        model_map = {
            "resume_quality": self.resume_quality,
            "application_quality": self.application_quality,
            "provider_quality": self.provider_quality,
            "job_quality": self.job_quality,
            "workflow_quality": self.workflow_quality,
        }
        scorer = model_map.get(model)
        if scorer is None:
            raise ScoringError(f"Unknown scoring model: {model}")
        return await scorer(data)

    async def resume_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {}

        if data.get("ats_score") is not None:
            components["ats_score"] = min(data["ats_score"] / 100.0, 1.0)
        if data.get("keyword_match") is not None:
            components["keyword_match"] = min(data["keyword_match"] / 100.0, 1.0)
        if data.get("formatting_score") is not None:
            components["formatting"] = min(data["formatting_score"] / 100.0, 1.0)
        if data.get("length_score") is not None:
            components["length"] = min(data["length_score"] / 100.0, 1.0)
        if data.get("completeness") is not None:
            components["completeness"] = min(data["completeness"], 1.0)
        if data.get("experience_relevance") is not None:
            components["experience_relevance"] = min(data["experience_relevance"], 1.0)
        if data.get("skill_coverage") is not None:
            components["skill_coverage"] = min(data["skill_coverage"], 1.0)

        if not components:
            components = {
                "ats_score": data.get("ats_score", 0) / 100.0,
                "completeness": data.get("completeness", 0.5),
                "formatting": data.get("formatting", 0.5),
            }

        weights = {
            "ats_score": 0.30,
            "keyword_match": 0.20,
            "formatting": 0.15,
            "length": 0.05,
            "completeness": 0.10,
            "experience_relevance": 0.10,
            "skill_coverage": 0.10,
        }
        total_weight = sum(weights.get(k, 1.0) for k in components)
        score = sum(components[k] * weights.get(k, 1.0) for k in components) / total_weight if total_weight > 0 else 0.0

        return {
            "score": round(score, 4),
            "components": components,
            "weights": {k: weights.get(k, 1.0) for k in components},
            "label": self._label(score),
            "model": "resume_quality",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def application_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {}

        if data.get("resume_quality") is not None:
            components["resume_quality"] = min(data["resume_quality"], 1.0)
        if data.get("cover_letter_quality") is not None:
            components["cover_letter_quality"] = min(data["cover_letter_quality"], 1.0)
        if data.get("match_score") is not None:
            components["match_score"] = min(data["match_score"] / 100.0, 1.0)
        if data.get("tailoring_score") is not None:
            components["tailoring"] = min(data["tailoring_score"] / 100.0, 1.0)
        if data.get("completeness") is not None:
            components["completeness"] = min(data["completeness"], 1.0)

        if not components:
            components = {
                "match_score": data.get("match_score", 50) / 100.0,
                "completeness": data.get("completeness", 0.5),
            }

        weights = {
            "resume_quality": 0.30,
            "cover_letter_quality": 0.20,
            "match_score": 0.30,
            "tailoring": 0.10,
            "completeness": 0.10,
        }
        total_weight = sum(weights.get(k, 1.0) for k in components)
        score = sum(components[k] * weights.get(k, 1.0) for k in components) / total_weight if total_weight > 0 else 0.0

        return {
            "score": round(score, 4),
            "components": components,
            "weights": {k: weights.get(k, 1.0) for k in components},
            "label": self._label(score),
            "model": "application_quality",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def provider_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {}

        if data.get("success_rate") is not None:
            components["success_rate"] = min(data["success_rate"], 1.0)
        if data.get("availability") is not None:
            components["availability"] = min(data["availability"], 1.0)
        if data.get("latency_score") is not None:
            components["latency"] = min(data["latency_score"], 1.0)
        if data.get("cost_score") is not None:
            components["cost"] = min(data["cost_score"], 1.0)
        if data.get("reliability") is not None:
            components["reliability"] = min(data["reliability"], 1.0)

        if not components:
            components = {"success_rate": data.get("success_rate", 0.5), "availability": data.get("availability", 0.5)}

        weights = {"success_rate": 0.35, "availability": 0.25, "latency": 0.20, "cost": 0.10, "reliability": 0.10}
        total_weight = sum(weights.get(k, 1.0) for k in components)
        score = sum(components[k] * weights.get(k, 1.0) for k in components) / total_weight if total_weight > 0 else 0.0

        return {
            "score": round(score, 4),
            "components": components,
            "weights": {k: weights.get(k, 1.0) for k in components},
            "label": self._label(score),
            "model": "provider_quality",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def job_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {}

        if data.get("match_score") is not None:
            components["match_score"] = min(data["match_score"] / 100.0, 1.0)
        if data.get("salary_score") is not None:
            components["salary"] = min(data["salary_score"] / 100.0, 1.0)
        if data.get("location_score") is not None:
            components["location"] = min(data["location_score"] / 100.0, 1.0)
        if data.get("company_score") is not None:
            components["company"] = min(data["company_score"] / 100.0, 1.0)
        if data.get("skill_match") is not None:
            components["skill_match"] = min(data["skill_match"] / 100.0, 1.0)

        if not components:
            components = {"match_score": data.get("match_score", 50) / 100.0}

        weights = {"match_score": 0.35, "salary": 0.15, "location": 0.15, "company": 0.20, "skill_match": 0.15}
        total_weight = sum(weights.get(k, 1.0) for k in components)
        score = sum(components[k] * weights.get(k, 1.0) for k in components) / total_weight if total_weight > 0 else 0.0

        return {
            "score": round(score, 4),
            "components": components,
            "weights": {k: weights.get(k, 1.0) for k in components},
            "label": self._label(score),
            "model": "job_quality",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def workflow_quality(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {}

        if data.get("automation_score") is not None:
            components["automation"] = min(data["automation_score"] / 100.0, 1.0)
        if data.get("reliability") is not None:
            components["reliability"] = min(data["reliability"], 1.0)
        if data.get("efficiency") is not None:
            components["efficiency"] = min(data["efficiency"], 1.0)
        if data.get("success_rate") is not None:
            components["success_rate"] = min(data["success_rate"], 1.0)
        if data.get("error_rate") is not None:
            components["error_rate"] = 1.0 - min(data["error_rate"], 1.0)

        if not components:
            components = {"success_rate": data.get("success_rate", 0.5), "reliability": data.get("reliability", 0.5)}

        weights = {
            "automation": 0.20,
            "reliability": 0.25,
            "efficiency": 0.20,
            "success_rate": 0.25,
            "error_rate": 0.10,
        }
        total_weight = sum(weights.get(k, 1.0) for k in components)
        score = sum(components[k] * weights.get(k, 1.0) for k in components) / total_weight if total_weight > 0 else 0.0

        return {
            "score": round(score, 4),
            "components": components,
            "weights": {k: weights.get(k, 1.0) for k in components},
            "label": self._label(score),
            "model": "workflow_quality",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def weighted_score(self, scores: list[dict[str, Any]]) -> dict[str, Any]:
        if not scores:
            raise ScoringError("No scores provided for weighted calculation")

        total_weight = sum(s.get("weight", 1.0) for s in scores)
        if total_weight == 0:
            raise ScoringError("Total weight must be greater than zero")

        weighted = sum(s.get("score", 0) * s.get("weight", 1.0) for s in scores) / total_weight

        return {
            "score": round(weighted, 4),
            "components": {s.get("name", f"component_{i}"): s.get("score", 0) for i, s in enumerate(scores)},
            "weights": {s.get("name", f"component_{i}"): s.get("weight", 1.0) for i, s in enumerate(scores)},
            "label": self._label(weighted),
            "model": "weighted",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def score_provider(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {
            "availability": min(data.get("availability", 0.0), 1.0),
            "latency": 1.0 - min(data.get("latency", 0) / 10000.0, 1.0),
            "cost": 1.0 - min(data.get("cost", 0) / 0.1, 1.0),
            "success_rate": min(data.get("success_rate", 0.0), 1.0),
            "error_rate": 1.0 - min(data.get("error_rate", 0.0), 1.0),
        }

        weights = {"availability": 0.20, "latency": 0.15, "cost": 0.15, "success_rate": 0.30, "error_rate": 0.20}
        score = sum(components[k] * weights[k] for k in components)

        return {
            "score": round(score, 4),
            "components": components,
            "weights": weights,
            "label": self._label(score),
            "model": "provider_score",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def score_prompt(self, data: dict[str, Any]) -> dict[str, Any]:
        components = {
            "quality": min(data.get("quality", 0.0), 1.0),
            "latency": 1.0 - min(data.get("latency", 0) / 10000.0, 1.0),
            "cost": 1.0 - min(data.get("cost", 0) / 0.1, 1.0),
            "success_rate": min(data.get("success_rate", 0.0), 1.0),
        }

        token_usage = data.get("token_usage", 0)
        if token_usage > 0:
            components["token_efficiency"] = 1.0 - min(token_usage / 4000.0, 1.0)

        weights = {"quality": 0.30, "latency": 0.15, "cost": 0.15, "success_rate": 0.30, "token_efficiency": 0.10}
        effective_weights = {k: v for k, v in weights.items() if k in components}
        total_weight = sum(effective_weights.values())
        score = (
            sum(components[k] * effective_weights[k] for k in components) / total_weight if total_weight > 0 else 0.0
        )

        return {
            "score": round(score, 4),
            "components": components,
            "weights": effective_weights,
            "label": self._label(score),
            "model": "prompt_score",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _label(score: float) -> str:
        if score >= 0.9:
            return "excellent"
        if score >= 0.75:
            return "good"
        if score >= 0.5:
            return "average"
        if score >= 0.25:
            return "below_average"
        return "poor"
