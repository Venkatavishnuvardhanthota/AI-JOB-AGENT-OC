from __future__ import annotations

from typing import Any

from app.forms.confidence import ConfidenceCalculator
from app.forms.schemas import (
    ExecutionPlan,
    FieldType,
    FormAnalysisResult,
    FormField,
    MappedField,
    MappingType,
    PlanStep,
    PlanStepType,
)


class PlanGenerator:
    def __init__(self, confidence_calculator: ConfidenceCalculator | None = None) -> None:
        self._confidence = confidence_calculator or ConfidenceCalculator()

    def generate(self, analysis: FormAnalysisResult, application_package: Any | None = None) -> ExecutionPlan:
        plan = ExecutionPlan()

        for mapping in analysis.mappings:
            step = self._create_step(mapping, analysis)
            plan.steps.append(step)
            self._tally_step(plan, step)

        plan.total_fields = len(analysis.fields)
        return plan

    def _create_step(self, mapping: MappedField, analysis: FormAnalysisResult) -> PlanStep:
        field = self._find_field(analysis, mapping.field_id)
        selector = field.selector if field else mapping.field_id
        field_type = field.field_type if field else FieldType.TEXT
        is_file = field_type == FieldType.FILE

        if mapping.mapping_type == MappingType.MAPPED:
            if is_file:
                return PlanStep(
                    step_type=PlanStepType.UPLOAD,
                    field_ref=mapping.field_id,
                    selector=selector,
                    source_path=mapping.source_path,
                    reason=mapping.reason,
                    confidence=mapping.confidence,
                )

            if field_type in (FieldType.SELECT, FieldType.RADIO):
                return PlanStep(
                    step_type=PlanStepType.SELECT,
                    field_ref=mapping.field_id,
                    selector=selector,
                    value=mapping.value,
                    source_path=mapping.source_path,
                    reason=mapping.reason,
                    confidence=mapping.confidence,
                )

            if field_type == FieldType.CHECKBOX:
                return PlanStep(
                    step_type=PlanStepType.CHECK,
                    field_ref=mapping.field_id,
                    selector=selector,
                    value=mapping.value,
                    source_path=mapping.source_path,
                    reason=mapping.reason,
                    confidence=mapping.confidence,
                )

            return PlanStep(
                step_type=PlanStepType.FILL,
                field_ref=mapping.field_id,
                selector=selector,
                value=mapping.value,
                source_path=mapping.source_path,
                reason=mapping.reason,
                confidence=mapping.confidence,
            )

        if mapping.mapping_type == MappingType.MISSING:
            return PlanStep(
                step_type=PlanStepType.REQUEST_MANUAL,
                field_ref=mapping.field_id,
                selector=selector,
                reason=mapping.reason or "Missing data for this field",
                requires_manual_review=True,
                confidence=mapping.confidence,
            )

        if mapping.mapping_type == MappingType.UNSUPPORTED:
            return PlanStep(
                step_type=PlanStepType.SKIP,
                field_ref=mapping.field_id,
                selector=selector,
                reason=mapping.reason or "Unsupported field type",
                confidence=mapping.confidence,
            )

        if mapping.mapping_type == MappingType.MANUAL:
            return PlanStep(
                step_type=PlanStepType.REQUEST_MANUAL,
                field_ref=mapping.field_id,
                selector=selector,
                reason=mapping.reason or "Manual input required",
                requires_manual_review=True,
                confidence=mapping.confidence,
            )

        return PlanStep(
            step_type=PlanStepType.SKIP,
            field_ref=mapping.field_id,
            selector=selector,
            reason="Unknown mapping type",
            requires_manual_review=True,
            confidence=mapping.confidence,
        )

    def _find_field(self, analysis: FormAnalysisResult, field_id: str) -> FormField | None:
        for field in analysis.fields:
            if field.id == field_id:
                return field
        return None

    def _tally_step(self, plan: ExecutionPlan, step: PlanStep) -> None:
        if step.step_type == PlanStepType.REQUEST_MANUAL:
            plan.requires_manual += 1
        elif step.step_type == PlanStepType.SKIP:
            plan.skipped += 1
        elif step.step_type == PlanStepType.UPLOAD:
            plan.uploads += 1
            plan.auto_fillable += 1
        else:
            plan.auto_fillable += 1
