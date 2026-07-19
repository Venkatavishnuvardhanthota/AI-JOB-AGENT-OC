from dataclasses import dataclass, field
from enum import Enum


class FormFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    RADIO = "radio"
    FILE = "file"


class ConsentStatus(str, Enum):
    PERMITTED = "permitted"
    NOT_PERMITTED = "not_permitted"
    UNKNOWN = "unknown"


@dataclass
class SiteFieldConfig:
    selector: str
    field_type: FormFieldType = FormFieldType.TEXT
    required: bool = False
    label: str | None = None
    placeholder: str | None = None


@dataclass
class SiteConfig:
    name: str
    url_pattern: str
    consent_status: ConsentStatus
    apply_url_pattern: str | None = None
    fields: list[SiteFieldConfig] = field(default_factory=list)
    resume_upload_selector: str | None = None
    cover_letter_upload_selector: str | None = None
    certificate_upload_selector: str | None = None
    submit_button_selector: str | None = None
    login_required: bool = False
    supports_file_upload: bool = False
    wait_after_navigation: float = 2.0
    wait_after_action: float = 1.0


@dataclass
class StepResult:
    step_name: str
    success: bool
    duration_ms: int = 0
    error: str | None = None
    screenshot_path: str | None = None


@dataclass
class AutomationResult:
    success: bool
    status: str
    steps: list[StepResult] = field(default_factory=list)
    error: str | None = None
    screenshot_paths: list[str] = field(default_factory=list)
    retry_count: int = 0
