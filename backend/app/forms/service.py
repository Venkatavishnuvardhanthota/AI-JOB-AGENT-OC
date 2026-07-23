from __future__ import annotations

from typing import Any

import structlog

from app.forms.analysis import FormAnalyzer
from app.forms.classification import FieldClassifier
from app.forms.confidence import ConfidenceCalculator
from app.forms.config import FormsConfig
from app.forms.exceptions import FormAnalysisError
from app.forms.factory import FormProviderFactory
from app.forms.interfaces import FormAnalyzer as FormAnalyzerInterface
from app.forms.mapping import FieldMapper
from app.forms.planning import PlanGenerator
from app.forms.registry import FormProviderRegistry
from app.forms.schemas import AnalyzeResponse, ExecutionPlan, FormAnalysisResult
from app.forms.validator import FormValidator

logger = structlog.get_logger(__name__)


class FormIntelligenceService:
    def __init__(
        self,
        registry: FormProviderRegistry,
        factory: FormProviderFactory,
        config: FormsConfig | None = None,
    ) -> None:
        self._registry = registry
        self._factory = factory
        self._config = config or FormsConfig()
        self._logger = logger.bind(service="form_intelligence")

        self._confidence = ConfidenceCalculator(self._config)
        self._classifier = FieldClassifier(self._confidence)
        self._analyzer = FormAnalyzer(self._classifier)
        self._mapper = FieldMapper(self._confidence)
        self._validator = FormValidator()
        self._planner = PlanGenerator(self._confidence)

    def analyze_form(self, page: Any, url: str) -> FormAnalysisResult:
        try:
            provider = self._get_provider_for_url(url)
            analysis = provider.analyze(page, url)

            for classification in analysis.classifications:
                field = self._find_field(analysis, classification.field_id)
                if field:
                    mapping = self._mapper.map_field(classification, field, None)
                    analysis.mappings.append(mapping)

            analysis.total_fields = len(analysis.fields)
            analysis.classified_count = len(analysis.classifications)
            analysis.mapped_count = sum(
                1 for m in analysis.mappings if m.mapping_type.value == "mapped"
            )
            analysis.missing_count = sum(
                1 for m in analysis.mappings if m.mapping_type.value == "missing"
            )
            analysis.requires_manual_count = sum(
                1 for m in analysis.mappings if m.requires_manual_review
            )

            analysis.validation_issues = self._validator.validate(analysis)

            return analysis
        except Exception as e:
            raise FormAnalysisError(f"Form analysis failed for {url}: {e}") from e

    def generate_plan(
        self,
        analysis: FormAnalysisResult,
        application_package: Any | None = None,
    ) -> ExecutionPlan:
        return self._planner.generate(analysis, application_package)

    def analyze_and_plan(
        self,
        page: Any,
        url: str,
        application_package: Any | None = None,
    ) -> AnalyzeResponse:
        analysis = self.analyze_form(page, url)
        plan = self.generate_plan(analysis, application_package)
        return AnalyzeResponse(analysis=analysis, plan=plan)

    def _get_provider_for_url(self, url: str) -> FormAnalyzerInterface:
        provider = self._factory.detect_provider(url)
        if provider is None:
            if self._registry.is_registered("default"):
                return self._registry.resolve("default")
            default = self._factory.create_provider("default")
            return default
        return provider

    def _find_field(self, analysis: FormAnalysisResult, field_id: str) -> Any:
        for field in analysis.fields:
            if field.id == field_id:
                return field
        return None
