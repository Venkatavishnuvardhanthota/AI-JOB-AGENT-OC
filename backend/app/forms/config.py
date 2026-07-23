from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FormsConfig:
    version: str = "1.0.0"
    min_confidence_for_auto: float = 0.85
    min_confidence_for_mapping: float = 0.60
    strict_validation: bool = True
    detect_hidden_fields: bool = False
    max_fields_per_form: int = 200
    classification_weights: dict[str, float] = field(
        default_factory=lambda: {
            "label_exact": 1.0,
            "label_normalized": 0.9,
            "placeholder": 0.7,
            "name_attr": 0.6,
            "id_attr": 0.5,
            "autocomplete": 0.85,
            "aria_label": 0.75,
            "regex_pattern": 0.65,
            "nearby_text": 0.4,
        }
    )
