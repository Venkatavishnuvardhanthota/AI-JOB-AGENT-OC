from __future__ import annotations

import uuid
from datetime import datetime, timezone
from statistics import mean
from typing import Any

import structlog

from app.intelligence.config import IntelligenceConfig
from app.intelligence.exceptions import ExperimentDataError

logger = structlog.get_logger(__name__)


class ExperimentEngine:
    def __init__(self, config: IntelligenceConfig) -> None:
        self._config = config
        self._experiments: dict[str, dict[str, Any]] = {}
        self._logger = logger.bind(engine="experiments")

    async def run(
        self, experiment_type: str, variant_a: str, variant_b: str, data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        if len(data) < self._config.experiment_sample_size_target:
            raise ExperimentDataError(
                f"Insufficient data: need at least {self._config.experiment_sample_size_target} samples, "
                f"got {len(data)}"
            )

        experiment_id = str(uuid.uuid4())
        self._logger.info(
            "Starting experiment",
            experiment_id=experiment_id,
            experiment_type=experiment_type,
            variant_a=variant_a,
            variant_b=variant_b,
            sample_size=len(data),
        )

        group_a = [d for d in data if d.get("variant") == variant_a or d.get("group") == "a"]
        group_b = [d for d in data if d.get("variant") == variant_b or d.get("group") == "b"]

        if not group_a or not group_b:
            groups = self._split_groups(data)
            group_a = groups["a"]
            group_b = groups["b"]

        metrics_a = self._compute_metrics(group_a)
        metrics_b = self._compute_metrics(group_b)

        winner = self._determine_winner(metrics_a, metrics_b)

        result = {
            "id": experiment_id,
            "type": experiment_type,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "winner": winner,
            "confidence": self._compute_confidence(metrics_a, metrics_b, winner),
            "metrics": {
                "a": metrics_a,
                "b": metrics_b,
            },
            "sample_size": len(data),
            "group_sizes": {"a": len(group_a), "b": len(group_b)},
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        self._experiments[experiment_id] = result
        self._logger.info("Experiment completed", experiment_id=experiment_id, winner=winner)

        return result

    async def get_results(self, experiment_id: str) -> dict[str, Any]:
        experiment = self._experiments.get(experiment_id)
        if experiment is None:
            raise ExperimentDataError(f"Experiment not found: {experiment_id}")
        return experiment

    async def list_experiments(self) -> list[dict[str, Any]]:
        return [
            {
                "id": eid,
                "type": exp["type"],
                "winner": exp.get("winner"),
                "confidence": exp.get("confidence"),
                "sample_size": exp.get("sample_size"),
                "started_at": exp.get("started_at"),
                "completed_at": exp.get("completed_at"),
            }
            for eid, exp in self._experiments.items()
        ]

    def _split_groups(self, data: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        mid = len(data) // 2
        return {"a": data[:mid], "b": data[mid:]}

    def _compute_metrics(self, group: list[dict[str, Any]]) -> dict[str, Any]:
        if not group:
            return {"success_rate": 0.0, "avg_quality": 0.0, "avg_latency": 0.0, "sample_size": 0}

        total = len(group)
        successful = sum(1 for d in group if d.get("status") == "success" or d.get("success") is True)
        qualities = [d.get("quality", 0) for d in group if d.get("quality") is not None]
        latencies = [d.get("latency", 0) for d in group if d.get("latency") is not None]

        return {
            "success_rate": round(successful / total, 4) if total > 0 else 0.0,
            "avg_quality": round(mean(qualities), 4) if qualities else 0.0,
            "avg_latency": round(mean(latencies), 2) if latencies else 0.0,
            "sample_size": total,
        }

    def _determine_winner(self, metrics_a: dict[str, Any], metrics_b: dict[str, Any]) -> str | None:
        if not metrics_a or not metrics_b:
            return None

        score_a = metrics_a["success_rate"] * 0.5 + metrics_a["avg_quality"] * 0.3 - metrics_a["avg_latency"] * 0.0002
        score_b = metrics_b["success_rate"] * 0.5 + metrics_b["avg_quality"] * 0.3 - metrics_b["avg_latency"] * 0.0002

        if score_a > score_b:
            return "a"
        if score_b > score_a:
            return "b"
        return None

    def _compute_confidence(self, metrics_a: dict[str, Any], metrics_b: dict[str, Any], winner: str | None) -> float:
        if winner is None:
            return 0.0

        key_a = metrics_a["success_rate"]
        key_b = metrics_b["success_rate"]
        diff = abs(key_a - key_b)

        n_a = max(metrics_a.get("sample_size", 1), 1)
        n_b = max(metrics_b.get("sample_size", 1), 1)
        total_n = n_a + n_b

        base_confidence = min(diff * 5.0, 1.0)
        size_factor = min(total_n / self._config.experiment_sample_size_target, 1.0)

        return round(base_confidence * size_factor, 4)
