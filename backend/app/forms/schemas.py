from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    DATE = "date"
    NUMBER = "number"
    PHONE = "tel"
    EMAIL = "email"
    URL = "url"
    HIDDEN = "hidden"
    AUTOCOMPLETE = "autocomplete"


class FieldState(BaseModel):
    required: bool = False
    readonly: bool = False
    disabled: bool = False
    visible: bool = True


class FormField(BaseModel):
    id: str
    selector: str
    field_type: FieldType
    state: FieldState = Field(default_factory=FieldState)
    label: str | None = None
    placeholder: str | None = None
    description: str | None = None
    group: str | None = None
    autocomplete: str | None = None
    options: list[str] = Field(default_factory=list)
    validation_rules: dict[str, Any] = Field(default_factory=dict)
    name: str | None = None
    value: str | None = None
    tag_name: str = "input"


class SemanticFieldType(str, Enum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FULL_NAME = "full_name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    COUNTRY = "country"
    ZIP_CODE = "zip_code"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    PORTFOLIO = "portfolio"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SCHOOL = "school"
    DEGREE = "degree"
    FIELD_OF_STUDY = "field_of_study"
    SKILLS = "skills"
    SALARY = "salary"
    NOTICE_PERIOD = "notice_period"
    VISA_STATUS = "visa_status"
    WORK_AUTHORIZATION = "work_authorization"
    RELOCATION = "relocation"
    REMOTE_PREFERENCE = "remote_preference"
    GRADUATION_DATE = "graduation_date"
    YEARS_OF_EXPERIENCE = "years_of_experience"
    EXPECTED_SALARY = "expected_salary"
    COMPANY = "company"
    JOB_TITLE = "job_title"
    WEBSITE = "website"
    HEADLINE = "headline"
    SUMMARY = "summary"
    LANGUAGE = "language"
    CERTIFICATION = "certification"
    GENDER = "gender"
    RACE = "race"
    VETERAN_STATUS = "veteran_status"
    DISABILITY = "disability"
    START_DATE = "start_date"
    END_DATE = "end_date"
    CUSTOM_QUESTION = "custom_question"
    UNKNOWN = "unknown"


class ConfidenceScore(BaseModel):
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    label_match: float = Field(default=0.0, ge=0.0, le=1.0)
    attribute_match: float = Field(default=0.0, ge=0.0, le=1.0)
    pattern_match: float = Field(default=0.0, ge=0.0, le=1.0)
    context_match: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""
    requires_review: bool = False


class ClassificationResult(BaseModel):
    field_id: str
    classification: SemanticFieldType
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    alternatives: list[SemanticFieldType] = Field(default_factory=list)


class MappingType(str, Enum):
    MAPPED = "mapped"
    MISSING = "missing"
    UNSUPPORTED = "unsupported"
    MANUAL = "manual"
    COMPUTED = "computed"


class MappedField(BaseModel):
    field_id: str
    classification: SemanticFieldType
    mapping_type: MappingType
    source_path: str | None = None
    value: Any = None
    transformation: str | None = None
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    requires_manual_review: bool = False
    fallback: str | None = None
    reason: str = ""


class ValidationIssue(BaseModel):
    severity: str = "warning"
    code: str = ""
    message: str = ""
    field_ids: list[str] = Field(default_factory=list)


class FormAnalysisResult(BaseModel):
    url: str = ""
    fields: list[FormField] = Field(default_factory=list)
    classifications: list[ClassificationResult] = Field(default_factory=list)
    mappings: list[MappedField] = Field(default_factory=list)
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    total_fields: int = 0
    classified_count: int = 0
    mapped_count: int = 0
    missing_count: int = 0
    requires_manual_count: int = 0


class PlanStepType(str, Enum):
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UPLOAD = "upload"
    SKIP = "skip"
    REQUEST_MANUAL = "request_manual"


class PlanStep(BaseModel):
    step_type: PlanStepType
    field_ref: str
    selector: str = ""
    value: Any = None
    source_path: str | None = None
    reason: str = ""
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    requires_manual_review: bool = False


class ExecutionPlan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)
    total_fields: int = 0
    auto_fillable: int = 0
    requires_manual: int = 0
    skipped: int = 0
    uploads: int = 0
    warnings: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    url: str
    provider_name: str | None = None


class AnalyzeResponse(BaseModel):
    analysis: FormAnalysisResult
    plan: ExecutionPlan
