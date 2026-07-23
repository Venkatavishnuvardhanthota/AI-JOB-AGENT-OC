from __future__ import annotations

from collections import Counter

from app.forms.schemas import (
    FormAnalysisResult,
    SemanticFieldType,
    ValidationIssue,
)


class FormValidator:
    def validate(self, analysis: FormAnalysisResult) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        issues.extend(self._check_duplicate_fields(analysis))
        issues.extend(self._check_missing_required(analysis))
        issues.extend(self._check_conflicting_mappings(analysis))
        issues.extend(self._check_ambiguous_labels(analysis))
        issues.extend(self._check_empty_form(analysis))
        return issues

    def _check_duplicate_fields(self, analysis: FormAnalysisResult) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        classifications = [
            c.classification.value for c in analysis.classifications
            if c.classification != SemanticFieldType.UNKNOWN
        ]
        dupes = {k: v for k, v in Counter(classifications).items() if v > 1}

        for semantic_type, count in dupes.items():
            field_ids = [
                c.field_id for c in analysis.classifications if c.classification.value == semantic_type
            ]
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="DUPLICATE_FIELD",
                    message=f"Field '{semantic_type}' appears {count} times",
                    field_ids=field_ids,
                )
            )

        return issues

    def _check_missing_required(self, analysis: FormAnalysisResult) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for field in analysis.fields:
            if field.state.required and not field.state.visible:
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        code="REQUIRED_FIELD_HIDDEN",
                        message=f"Required field '{field.label or field.name or field.id}' is not visible",
                        field_ids=[field.id],
                    )
                )
        return issues

    def _check_conflicting_mappings(self, analysis: FormAnalysisResult) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        source_paths: dict[str, list[str]] = {}
        for mapping in analysis.mappings:
            if mapping.source_path:
                if mapping.source_path not in source_paths:
                    source_paths[mapping.source_path] = []
                source_paths[mapping.source_path].append(mapping.field_id)

        for source_path, field_ids in source_paths.items():
            if len(field_ids) > 1:
                issues.append(
                    ValidationIssue(
                        severity="error" if len(field_ids) > 2 else "warning",
                        code="CONFLICTING_MAPPING",
                        message=f"Source path '{source_path}' maps to {len(field_ids)} fields",
                        field_ids=field_ids,
                    )
                )

        return issues

    def _check_ambiguous_labels(self, analysis: FormAnalysisResult) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        fields_without_label = [
            f for f in analysis.fields
            if not f.label and f.field_type.value != "hidden"
        ]
        if len(fields_without_label) > 1:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    code="AMBIGUOUS_LABELS",
                    message=f"{len(fields_without_label)} fields have no discernible label",
                    field_ids=[f.id for f in fields_without_label],
                )
            )
        return issues

    def _check_empty_form(self, analysis: FormAnalysisResult) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if not analysis.fields:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="EMPTY_FORM",
                    message="No form fields detected on the page",
                )
            )
        return issues
