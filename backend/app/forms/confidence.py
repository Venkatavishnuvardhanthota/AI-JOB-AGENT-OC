from __future__ import annotations

from app.forms.config import FormsConfig
from app.forms.schemas import ConfidenceScore


class ConfidenceCalculator:
    def __init__(self, config: FormsConfig | None = None) -> None:
        self._config = config or FormsConfig()

    def calculate(
        self,
        label_match: float = 0.0,
        attribute_match: float = 0.0,
        pattern_match: float = 0.0,
        context_match: float = 0.0,
        reason: str = "",
    ) -> ConfidenceScore:
        weights = self._config.classification_weights
        weight_total = 0.0
        weighted_sum = 0.0

        signal_pairs = [
            ("label_exact", label_match),
            ("name_attr", attribute_match),
            ("regex_pattern", pattern_match),
            ("nearby_text", context_match),
        ]

        for weight_key, signal_value in signal_pairs:
            w = weights.get(weight_key, 0.5)
            if signal_value > 0:
                weight_total += w
            weighted_sum += signal_value * w

        overall = weighted_sum / max(weight_total, 0.001)
        overall = max(0.0, min(1.0, overall))
        requires_review = overall < self._config.min_confidence_for_auto

        return ConfidenceScore(
            overall=round(overall, 4),
            label_match=round(max(0.0, min(1.0, label_match)), 4),
            attribute_match=round(max(0.0, min(1.0, attribute_match)), 4),
            pattern_match=round(max(0.0, min(1.0, pattern_match)), 4),
            context_match=round(max(0.0, min(1.0, context_match)), 4),
            reason=reason,
            requires_review=requires_review,
        )

    def combine(self, scores: list[ConfidenceScore]) -> ConfidenceScore:
        if not scores:
            return ConfidenceScore()
        avg_overall = sum(s.overall for s in scores) / len(scores)
        avg_label = sum(s.label_match for s in scores) / len(scores)
        avg_attr = sum(s.attribute_match for s in scores) / len(scores)
        avg_pattern = sum(s.pattern_match for s in scores) / len(scores)
        avg_context = sum(s.context_match for s in scores) / len(scores)
        reasons = [s.reason for s in scores if s.reason]
        return ConfidenceScore(
            overall=round(avg_overall, 4),
            label_match=round(avg_label, 4),
            attribute_match=round(avg_attr, 4),
            pattern_match=round(avg_pattern, 4),
            context_match=round(avg_context, 4),
            requires_review=avg_overall < self._config.min_confidence_for_auto,
            reason="; ".join(reasons) if reasons else "",
        )
