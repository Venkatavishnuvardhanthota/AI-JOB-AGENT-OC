from __future__ import annotations

import re

from app.forms.confidence import ConfidenceCalculator
from app.forms.normalization import lookup_normalized, normalize_label
from app.forms.schemas import (
    ClassificationResult,
    ConfidenceScore,
    FieldType,
    FormField,
    SemanticFieldType,
)

_AUTOCOMPLETE_MAP: dict[str, SemanticFieldType] = {
    "given-name": SemanticFieldType.FIRST_NAME,
    "family-name": SemanticFieldType.LAST_NAME,
    "name": SemanticFieldType.FULL_NAME,
    "email": SemanticFieldType.EMAIL,
    "tel": SemanticFieldType.PHONE,
    "tel-national": SemanticFieldType.PHONE,
    "street-address": SemanticFieldType.ADDRESS,
    "address-line1": SemanticFieldType.ADDRESS,
    "address-line2": SemanticFieldType.ADDRESS,
    "address-level1": SemanticFieldType.STATE,
    "address-level2": SemanticFieldType.CITY,
    "postal-code": SemanticFieldType.ZIP_CODE,
    "country-name": SemanticFieldType.COUNTRY,
    "organization": SemanticFieldType.COMPANY,
    "organization-title": SemanticFieldType.JOB_TITLE,
    "url": SemanticFieldType.WEBSITE,
    "bday": SemanticFieldType.GRADUATION_DATE,
    "bday-year": SemanticFieldType.GRADUATION_DATE,
    "language": SemanticFieldType.LANGUAGE,
    "tel-country-code": SemanticFieldType.PHONE,
}

_NAME_PATTERNS: list[tuple[re.Pattern, SemanticFieldType, float]] = [
    (re.compile(r"^first[-_]?name$", re.I), SemanticFieldType.FIRST_NAME, 0.9),
    (re.compile(r"^last[-_]?name$", re.I), SemanticFieldType.LAST_NAME, 0.9),
    (re.compile(r"^full[-_]?name$", re.I), SemanticFieldType.FULL_NAME, 0.9),
    (re.compile(r"^user[-_]?email$", re.I), SemanticFieldType.EMAIL, 0.85),
    (re.compile(r"^email$", re.I), SemanticFieldType.EMAIL, 0.95),
    (re.compile(r"^e[-_]?mail$", re.I), SemanticFieldType.EMAIL, 0.9),
    (re.compile(r"^phone$", re.I), SemanticFieldType.PHONE, 0.95),
    (re.compile(r"^telephone$", re.I), SemanticFieldType.PHONE, 0.9),
    (re.compile(r"^mobile$", re.I), SemanticFieldType.PHONE, 0.85),
    (re.compile(r"^phone[-_]?number$", re.I), SemanticFieldType.PHONE, 0.9),
    (re.compile(r"^linkedin$", re.I), SemanticFieldType.LINKEDIN, 0.85),
    (re.compile(r"^linkedin[-_]?url$", re.I), SemanticFieldType.LINKEDIN, 0.9),
    (re.compile(r"^github$", re.I), SemanticFieldType.GITHUB, 0.85),
    (re.compile(r"^github[-_]?url$", re.I), SemanticFieldType.GITHUB, 0.9),
    (re.compile(r"^portfolio[-_]?url$", re.I), SemanticFieldType.PORTFOLIO, 0.85),
    (re.compile(r"^website$", re.I), SemanticFieldType.WEBSITE, 0.7),
    (re.compile(r"^resume$", re.I), SemanticFieldType.RESUME, 0.9),
    (re.compile(r"^cv$", re.I), SemanticFieldType.RESUME, 0.85),
    (re.compile(r"^cover[-_]?letter$", re.I), SemanticFieldType.COVER_LETTER, 0.9),
    (re.compile(r"^salary[-_]?expect", re.I), SemanticFieldType.EXPECTED_SALARY, 0.85),
    (re.compile(r"^desired[-_]?salary", re.I), SemanticFieldType.EXPECTED_SALARY, 0.85),
    (re.compile(r"^current[-_]?salary", re.I), SemanticFieldType.SALARY, 0.85),
    (re.compile(r"^years[-_]?of[-_]?experience", re.I), SemanticFieldType.YEARS_OF_EXPERIENCE, 0.85),
    (re.compile(r"^work[-_]?experience", re.I), SemanticFieldType.EXPERIENCE, 0.7),
    (re.compile(r"^education$", re.I), SemanticFieldType.EDUCATION, 0.7),
    (re.compile(r"^skills$", re.I), SemanticFieldType.SKILLS, 0.7),
    (re.compile(r"^address$", re.I), SemanticFieldType.ADDRESS, 0.7),
    (re.compile(r"^city$", re.I), SemanticFieldType.CITY, 0.85),
    (re.compile(r"^state$", re.I), SemanticFieldType.STATE, 0.8),
    (re.compile(r"^country$", re.I), SemanticFieldType.COUNTRY, 0.85),
    (re.compile(r"^zip[-_]?code$", re.I), SemanticFieldType.ZIP_CODE, 0.85),
    (re.compile(r"^postal[-_]?code$", re.I), SemanticFieldType.ZIP_CODE, 0.85),
    (re.compile(r"^notice[-_]?period$", re.I), SemanticFieldType.NOTICE_PERIOD, 0.85),
    (re.compile(r"^visa[-_]?(status|sponsorship)", re.I), SemanticFieldType.VISA_STATUS, 0.8),
    (re.compile(r"^work[-_]?authorization", re.I), SemanticFieldType.WORK_AUTHORIZATION, 0.8),
    (re.compile(r"^relocation$", re.I), SemanticFieldType.RELOCATION, 0.8),
    (re.compile(r"^remote[-_]?preference", re.I), SemanticFieldType.REMOTE_PREFERENCE, 0.8),
    (re.compile(r"^graduation[-_]?date", re.I), SemanticFieldType.GRADUATION_DATE, 0.85),
    (re.compile(r"^company$", re.I), SemanticFieldType.COMPANY, 0.7),
    (re.compile(r"^employer$", re.I), SemanticFieldType.COMPANY, 0.7),
    (re.compile(r"^job[-_]?title$", re.I), SemanticFieldType.JOB_TITLE, 0.8),
    (re.compile(r"^position$", re.I), SemanticFieldType.JOB_TITLE, 0.7),
    (re.compile(r"^headline$", re.I), SemanticFieldType.HEADLINE, 0.6),
    (re.compile(r"^summary$", re.I), SemanticFieldType.SUMMARY, 0.6),
    (re.compile(r"^language$", re.I), SemanticFieldType.LANGUAGE, 0.7),
    (re.compile(r"^certification", re.I), SemanticFieldType.CERTIFICATION, 0.7),
    (re.compile(r"^gender$", re.I), SemanticFieldType.GENDER, 0.85),
    (re.compile(r"^race$", re.I), SemanticFieldType.RACE, 0.8),
    (re.compile(r"^ethnicity$", re.I), SemanticFieldType.RACE, 0.8),
    (re.compile(r"^veteran", re.I), SemanticFieldType.VETERAN_STATUS, 0.8),
    (re.compile(r"^disability", re.I), SemanticFieldType.DISABILITY, 0.8),
    (re.compile(r"^start[-_]?date", re.I), SemanticFieldType.START_DATE, 0.85),
    (re.compile(r"^end[-_]?date", re.I), SemanticFieldType.END_DATE, 0.85),
    (re.compile(r"^school$", re.I), SemanticFieldType.SCHOOL, 0.75),
    (re.compile(r"^university$", re.I), SemanticFieldType.SCHOOL, 0.75),
    (re.compile(r"^degree$", re.I), SemanticFieldType.DEGREE, 0.7),
    (re.compile(r"^major$", re.I), SemanticFieldType.FIELD_OF_STUDY, 0.7),
    (re.compile(r"^field[-_]?of[-_]?study", re.I), SemanticFieldType.FIELD_OF_STUDY, 0.8),
    (re.compile(r"^first[-_]?name$", re.I), SemanticFieldType.FIRST_NAME, 0.95),
    (re.compile(r"^last[-_]?name$", re.I), SemanticFieldType.LAST_NAME, 0.95),
]

_ID_PATTERNS: list[tuple[re.Pattern, SemanticFieldType, float]] = [
    (re.compile(r"(?:^|[-_])first[-_]?name(?:$|[-_])", re.I), SemanticFieldType.FIRST_NAME, 0.7),
    (re.compile(r"(?:^|[-_])last[-_]?name(?:$|[-_])", re.I), SemanticFieldType.LAST_NAME, 0.7),
    (re.compile(r"(?:^|[-_])email(?:$|[-_])", re.I), SemanticFieldType.EMAIL, 0.8),
    (re.compile(r"(?:^|[-_])phone(?:$|[-_])", re.I), SemanticFieldType.PHONE, 0.8),
    (re.compile(r"(?:^|[-_])linkedin(?:$|[-_])", re.I), SemanticFieldType.LINKEDIN, 0.6),
    (re.compile(r"(?:^|[-_])github(?:$|[-_])", re.I), SemanticFieldType.GITHUB, 0.6),
    (re.compile(r"(?:^|[-_])resume(?:$|[-_])", re.I), SemanticFieldType.RESUME, 0.7),
    (re.compile(r"(?:^|[-_])cover[-_]?letter", re.I), SemanticFieldType.COVER_LETTER, 0.7),
    (re.compile(r"input[-_]?salary", re.I), SemanticFieldType.EXPECTED_SALARY, 0.6),
    (re.compile(r"input[-_]?file", re.I), SemanticFieldType.RESUME, 0.4),
    (re.compile(r"(?:^|[-_])address(?:$|[-_])", re.I), SemanticFieldType.ADDRESS, 0.5),
    (re.compile(r"(?:^|[-_])city(?:$|[-_])", re.I), SemanticFieldType.CITY, 0.7),
    (re.compile(r"(?:^|[-_])state(?:$|[-_])", re.I), SemanticFieldType.STATE, 0.6),
    (re.compile(r"(?:^|[-_])country(?:$|[-_])", re.I), SemanticFieldType.COUNTRY, 0.7),
    (re.compile(r"(?:^|[-_])zip(?:$|[-_])", re.I), SemanticFieldType.ZIP_CODE, 0.6),
    (re.compile(r"(?:^|[-_])skill", re.I), SemanticFieldType.SKILLS, 0.5),
    (re.compile(r"(?:^|[-_])education", re.I), SemanticFieldType.EDUCATION, 0.5),
    (re.compile(r"(?:^|[-_])experience", re.I), SemanticFieldType.EXPERIENCE, 0.5),
    (re.compile(r"(?:^|[-_])company(?:$|[-_])", re.I), SemanticFieldType.COMPANY, 0.5),
    (re.compile(r"(?:^|[-_])position(?:$|[-_])", re.I), SemanticFieldType.JOB_TITLE, 0.5),
    (re.compile(r"(?:^|[-_])title(?:$|[-_])", re.I), SemanticFieldType.JOB_TITLE, 0.4),
]

_PLACEHOLDER_PATTERNS: list[tuple[re.Pattern, SemanticFieldType, float]] = [
    (re.compile(r"first\s*name", re.I), SemanticFieldType.FIRST_NAME, 0.6),
    (re.compile(r"last\s*name", re.I), SemanticFieldType.LAST_NAME, 0.6),
    (re.compile(r"email", re.I), SemanticFieldType.EMAIL, 0.7),
    (re.compile(r"phone", re.I), SemanticFieldType.PHONE, 0.6),
    (re.compile(r"linkedin", re.I), SemanticFieldType.LINKEDIN, 0.5),
    (re.compile(r"github", re.I), SemanticFieldType.GITHUB, 0.5),
    (re.compile(r"resume", re.I), SemanticFieldType.RESUME, 0.5),
    (re.compile(r"cover\s*letter", re.I), SemanticFieldType.COVER_LETTER, 0.5),
    (re.compile(r"address", re.I), SemanticFieldType.ADDRESS, 0.4),
    (re.compile(r"city", re.I), SemanticFieldType.CITY, 0.5),
    (re.compile(r"state", re.I), SemanticFieldType.STATE, 0.4),
    (re.compile(r"zip", re.I), SemanticFieldType.ZIP_CODE, 0.4),
    (re.compile(r"company", re.I), SemanticFieldType.COMPANY, 0.4),
    (re.compile(r"position", re.I), SemanticFieldType.JOB_TITLE, 0.4),
    (re.compile(r"salary", re.I), SemanticFieldType.EXPECTED_SALARY, 0.4),
]


class FieldClassifier:
    def __init__(self, confidence_calculator: ConfidenceCalculator | None = None) -> None:
        self._confidence = confidence_calculator or ConfidenceCalculator()

    def classify(self, field: FormField, context: list[FormField] | None = None) -> ClassificationResult:
        best: tuple[SemanticFieldType, ConfidenceScore] | None = None
        alternatives: list[SemanticFieldType] = []

        result = self._classify_by_label(field)
        if result:
            st, cs = result
            best = (st, cs)
            alternatives.append(st)

        result = self._classify_by_autocomplete(field)
        if result:
            st, cs = result
            if best is None or cs.overall > best[1].overall:
                alternatives.append(st)
                best = (st, cs)
            elif cs.overall > 0.5:
                alternatives.append(st)

        result = self._classify_by_name(field)
        if result:
            st, cs = result
            if best is None or cs.overall > best[1].overall:
                alternatives.append(st)
                best = (st, cs)
            elif cs.overall > 0.5 and st not in alternatives:
                alternatives.append(st)

        result = self._classify_by_id(field)
        if result:
            st, cs = result
            if best is None or cs.overall > best[1].overall:
                alternatives.append(st)
                best = (st, cs)
            elif cs.overall > 0.5 and st not in alternatives:
                alternatives.append(st)

        result = self._classify_by_placeholder(field)
        if result:
            st, cs = result
            if best is None or cs.overall > best[1].overall:
                alternatives.append(st)
                best = (st, cs)
            elif cs.overall > 0.5 and st not in alternatives:
                alternatives.append(st)

        result = self._classify_by_field_type(field)
        if result:
            st, cs = result
            if best is None or cs.overall > best[1].overall:
                if st not in alternatives:
                    alternatives.append(st)
                best = (st, cs)
            elif cs.overall > 0.3 and st not in alternatives:
                alternatives.append(st)

        if best is None:
            best = (SemanticFieldType.UNKNOWN, ConfidenceScore(
                overall=0.1,
                reason="No classification signals found.",
                requires_review=True,
            ))

        final_confidence = self._adjust_confidence_for_field_type(field, best[1])

        return ClassificationResult(
            field_id=field.id,
            classification=best[0],
            confidence=final_confidence,
            alternatives=[a for a in alternatives if a != best[0]][:3],
        )

    def _classify_by_label(self, field: FormField) -> tuple[SemanticFieldType, ConfidenceScore] | None:
        if not field.label:
            return None
        normalized = normalize_label(field.label)
        mapped = lookup_normalized(normalized)
        if mapped:
            try:
                st = SemanticFieldType(mapped)
                return st, self._confidence.calculate(
                    label_match=0.95,
                    reason=f"Label '{field.label}' matches '{mapped}'",
                )
            except ValueError:
                pass

        for pattern, st, score in _NAME_PATTERNS:
            if pattern.search(normalized):
                return st, self._confidence.calculate(
                    label_match=score,
                    reason=f"Label pattern matched '{st.value}'",
                )

        return None

    def _classify_by_autocomplete(self, field: FormField) -> tuple[SemanticFieldType, ConfidenceScore] | None:
        if not field.autocomplete:
            return None
        ac = field.autocomplete.lower().strip()
        if ac in _AUTOCOMPLETE_MAP:
            st = _AUTOCOMPLETE_MAP[ac]
            return st, self._confidence.calculate(
                attribute_match=0.85,
                reason=f"Autocomplete attribute '{ac}' maps to '{st.value}'",
            )
        return None

    def _classify_by_name(self, field: FormField) -> tuple[SemanticFieldType, ConfidenceScore] | None:
        if not field.name:
            return None
        for pattern, st, score in _NAME_PATTERNS:
            if pattern.search(field.name):
                return st, self._confidence.calculate(
                    attribute_match=score * 0.9,
                    reason=f"Name attribute '{field.name}' matches '{st.value}'",
                )
        return None

    def _classify_by_id(self, field: FormField) -> tuple[SemanticFieldType, ConfidenceScore] | None:
        if not field.id or field.id == field.name:
            return None
        for pattern, st, score in _ID_PATTERNS:
            if pattern.search(field.id):
                return st, self._confidence.calculate(
                    attribute_match=score,
                    reason=f"ID attribute '{field.id}' matches '{st.value}'",
                )
        return None

    def _classify_by_placeholder(self, field: FormField) -> tuple[SemanticFieldType, ConfidenceScore] | None:
        if not field.placeholder:
            return None

        normalized = normalize_label(field.placeholder)
        mapped = lookup_normalized(normalized)
        if mapped:
            try:
                st = SemanticFieldType(mapped)
                return st, self._confidence.calculate(
                    pattern_match=0.7,
                    reason=f"Placeholder '{field.placeholder}' matches '{mapped}'",
                )
            except ValueError:
                pass

        for pattern, st, score in _PLACEHOLDER_PATTERNS:
            if pattern.search(field.placeholder):
                return st, self._confidence.calculate(
                    pattern_match=score,
                    reason=f"Placeholder pattern matched '{st.value}'",
                )
        return None

    def _classify_by_field_type(self, field: FormField) -> tuple[SemanticFieldType, ConfidenceScore] | None:
        if field.field_type.value == "file":
            return SemanticFieldType.RESUME, self._confidence.calculate(
                context_match=0.3,
                reason="File upload field, likely resume upload",
            )
        if field.field_type.value == "tel":
            return SemanticFieldType.PHONE, self._confidence.calculate(
                pattern_match=0.5,
                reason="Telephone input type",
            )
        if field.field_type.value == "email":
            return SemanticFieldType.EMAIL, self._confidence.calculate(
                pattern_match=0.6,
                reason="Email input type",
            )
        if field.field_type.value == "url":
            return SemanticFieldType.WEBSITE, self._confidence.calculate(
                pattern_match=0.4,
                reason="URL input type",
            )
        return None

    def _adjust_confidence_for_field_type(self, field: FormField, confidence: ConfidenceScore) -> ConfidenceScore:
        adjusted = confidence.model_copy()
        if field.state.disabled or field.state.readonly:
            adjusted.overall *= 0.5
            adjusted.reason += " [field is disabled/readonly]"
        if field.field_type == FieldType.HIDDEN:
            adjusted.overall *= 0.3
            adjusted.reason += " [field is hidden]"
        return adjusted
