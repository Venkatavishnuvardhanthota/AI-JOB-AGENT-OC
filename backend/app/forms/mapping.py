from __future__ import annotations

from typing import Any

from app.forms.confidence import ConfidenceCalculator
from app.forms.schemas import (
    ClassificationResult,
    ConfidenceScore,
    FormField,
    MappedField,
    MappingType,
    SemanticFieldType,
)

_RESUME_FIELDS = {SemanticFieldType.RESUME, SemanticFieldType.COVER_LETTER}
_PERSONAL_INFO_FIELDS = {
    SemanticFieldType.FIRST_NAME: "profile.personal_info.first_name",
    SemanticFieldType.LAST_NAME: "profile.personal_info.last_name",
    SemanticFieldType.FULL_NAME: "profile.personal_info.full_name",
    SemanticFieldType.EMAIL: "profile.personal_info.email",
    SemanticFieldType.PHONE: "profile.personal_info.phone",
    SemanticFieldType.ADDRESS: "profile.personal_info.address",
    SemanticFieldType.CITY: "profile.personal_info.city",
    SemanticFieldType.STATE: "profile.personal_info.state",
    SemanticFieldType.COUNTRY: "profile.personal_info.country",
    SemanticFieldType.ZIP_CODE: "profile.personal_info.zip_code",
    SemanticFieldType.LINKEDIN: "profile.personal_info.linkedin",
    SemanticFieldType.GITHUB: "profile.personal_info.github",
    SemanticFieldType.PORTFOLIO: "profile.personal_info.portfolio",
    SemanticFieldType.WEBSITE: "profile.personal_info.website",
    SemanticFieldType.HEADLINE: "profile.personal_info.headline",
    SemanticFieldType.SUMMARY: "profile.personal_info.summary",
    SemanticFieldType.LANGUAGE: "profile.personal_info.languages",
}
_PROFESSIONAL_FIELDS = {
    SemanticFieldType.COMPANY: "profile.experience[0].company",
    SemanticFieldType.JOB_TITLE: "profile.experience[0].title",
    SemanticFieldType.EXPERIENCE: "profile.experience",
    SemanticFieldType.YEARS_OF_EXPERIENCE: "profile.experience[0].years",
    SemanticFieldType.START_DATE: "profile.experience[0].start_date",
    SemanticFieldType.END_DATE: "profile.experience[0].end_date",
    SemanticFieldType.SKILLS: "profile.skills",
    SemanticFieldType.EDUCATION: "profile.education",
    SemanticFieldType.SCHOOL: "profile.education[0].school",
    SemanticFieldType.DEGREE: "profile.education[0].degree",
    SemanticFieldType.FIELD_OF_STUDY: "profile.education[0].field_of_study",
    SemanticFieldType.GRADUATION_DATE: "profile.education[0].graduation_date",
    SemanticFieldType.CERTIFICATION: "profile.certifications",
}
_PREFERENCE_FIELDS = {
    SemanticFieldType.EXPECTED_SALARY: "profile.preferences.expected_salary",
    SemanticFieldType.SALARY: "profile.preferences.current_salary",
    SemanticFieldType.NOTICE_PERIOD: "profile.preferences.notice_period",
    SemanticFieldType.VISA_STATUS: "profile.preferences.visa_status",
    SemanticFieldType.WORK_AUTHORIZATION: "profile.preferences.work_authorization",
    SemanticFieldType.RELOCATION: "profile.preferences.relocation_willing",
    SemanticFieldType.REMOTE_PREFERENCE: "profile.preferences.remote_preference",
}
_OTHER_FIELDS = {
    SemanticFieldType.GENDER: "profile.demographics.gender",
    SemanticFieldType.RACE: "profile.demographics.race",
    SemanticFieldType.VETERAN_STATUS: "profile.demographics.veteran_status",
    SemanticFieldType.DISABILITY: "profile.demographics.disability",
}
_ALL_MAPPINGS: dict[SemanticFieldType, str] = {}
_ALL_MAPPINGS.update(_PERSONAL_INFO_FIELDS)
_ALL_MAPPINGS.update(_PROFESSIONAL_FIELDS)
_ALL_MAPPINGS.update(_PREFERENCE_FIELDS)
_ALL_MAPPINGS.update(_OTHER_FIELDS)

_RESUME_SOURCE = "resume"
_COVER_LETTER_SOURCE = "cover_letter"


class FieldMapper:
    def __init__(self, confidence_calculator: ConfidenceCalculator | None = None) -> None:
        self._confidence = confidence_calculator or ConfidenceCalculator()

    def map_field(
        self,
        classification: ClassificationResult,
        field: FormField,
        application_package: Any,
    ) -> MappedField:
        st = classification.classification

        if st in _RESUME_FIELDS:
            return self._map_resume_field(classification, field, st)

        if st in _ALL_MAPPINGS:
            return self._map_structured_field(classification, st, field, application_package)

        if st == SemanticFieldType.CUSTOM_QUESTION:
            return MappedField(
                field_id=classification.field_id,
                classification=st,
                mapping_type=MappingType.MANUAL,
                confidence=classification.confidence,
                requires_manual_review=True,
                reason="Custom question requires manual review",
            )

        return MappedField(
            field_id=classification.field_id,
            classification=st,
            mapping_type=MappingType.UNSUPPORTED,
            confidence=classification.confidence,
            requires_manual_review=True,
            reason=f"Unsupported field type: {st.value}",
        )

    def _map_resume_field(
        self,
        classification: ClassificationResult,
        field: FormField,
        st: SemanticFieldType,
    ) -> MappedField:
        is_upload = field.field_type.value == "file"
        source = _RESUME_SOURCE if st == SemanticFieldType.RESUME else _COVER_LETTER_SOURCE

        if is_upload:
            return MappedField(
                field_id=classification.field_id,
                classification=st,
                mapping_type=MappingType.MAPPED,
                source_path=source,
                confidence=ConfidenceScore(
                    overall=0.9,
                    label_match=0.9,
                    reason="File upload field mapped to resume/cover letter",
                ),
                reason=f"Mapped to {source} upload",
            )

        return MappedField(
            field_id=classification.field_id,
            classification=st,
            mapping_type=MappingType.MAPPED,
            source_path=source,
            transformation="render_to_text",
            confidence=ConfidenceScore(
                overall=0.7,
                label_match=0.7,
                reason=f"Mapped to {source} content",
            ),
            reason=f"Mapped to {source} (text)",
        )

    def _map_structured_field(
        self,
        classification: ClassificationResult,
        st: SemanticFieldType,
        field: FormField,
        application_package: Any,
    ) -> MappedField:
        source_path = _ALL_MAPPINGS.get(st)
        value = self._resolve_value(application_package, source_path) if source_path else None

        if value is not None:
            return MappedField(
                field_id=classification.field_id,
                classification=st,
                mapping_type=MappingType.MAPPED,
                source_path=source_path,
                value=value,
                confidence=self._confidence.calculate(
                    label_match=classification.confidence.overall,
                    reason=f"Mapped to {source_path}",
                ),
                reason=f"Data available at {source_path}",
            )

        return MappedField(
            field_id=classification.field_id,
            classification=st,
            mapping_type=MappingType.MISSING,
            source_path=source_path,
            confidence=self._confidence.calculate(
                label_match=classification.confidence.overall * 0.5,
                reason=f"Field '{st.value}' not found in application package",
            ),
            requires_manual_review=True,
            reason=f"No data found at {source_path}",
            fallback=f"Request manual input for {st.value}",
        )

    def _resolve_value(self, application_package: Any, source_path: str) -> Any:
        if application_package is None:
            return None
        parts = source_path.split(".")
        current = application_package
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    idx = int(part.strip("[]"))
                    current = current[idx] if idx < len(current) else None
                except (ValueError, IndexError):
                    try:
                        current = getattr(current, part, None)
                    except Exception:
                        return None
            else:
                try:
                    current = getattr(current, part, None)
                except Exception:
                    return None

            if current is None:
                return None

        if isinstance(current, str | int | float | bool):
            return current
        if isinstance(current, list):
            return ", ".join(str(c) for c in current if c is not None)
        if hasattr(current, "model_dump"):
            return current.model_dump()
        return str(current) if current is not None else None
