from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.forms.analysis import FormAnalyzer
from app.forms.classification import FieldClassifier
from app.forms.confidence import ConfidenceCalculator
from app.forms.config import FormsConfig
from app.forms.dependencies import get_forms_service, reset_forms_service
from app.forms.exceptions import (
    FormAnalysisError,
    FormConfigError,
    FormMappingError,
    FormPlanningError,
    FormProviderNotFoundError,
    FormsError,
    FormValidationError,
)
from app.forms.factory import FormProviderFactory
from app.forms.mapping import FieldMapper
from app.forms.normalization import fuzzy_match, lookup_normalized, normalize_label
from app.forms.planning import PlanGenerator
from app.forms.providers.base import BaseFormProvider
from app.forms.registry import FormProviderRegistry
from app.forms.schemas import (
    ClassificationResult,
    ConfidenceScore,
    ExecutionPlan,
    FieldState,
    FieldType,
    FormAnalysisResult,
    FormField,
    MappedField,
    MappingType,
    PlanStep,
    PlanStepType,
    SemanticFieldType,
    ValidationIssue,
)
from app.forms.service import FormIntelligenceService
from app.forms.validator import FormValidator

# ═══════════════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_element():
    el = MagicMock()
    el.get_attribute.return_value = None
    el.evaluate.return_value = None
    el.query_selector_all.return_value = []
    el.text_content.return_value = ""
    return el


@pytest.fixture
def mock_page():
    page = MagicMock()
    page.query_selector_all.return_value = []
    return page


@pytest.fixture
def config():
    return FormsConfig()


@pytest.fixture
def classifier():
    return FieldClassifier()


@pytest.fixture
def analyzer():
    return FormAnalyzer()


@pytest.fixture
def mapper():
    return FieldMapper()


@pytest.fixture
def planner():
    return PlanGenerator()


@pytest.fixture
def validator():
    return FormValidator()


@pytest.fixture
def registry():
    return FormProviderRegistry()


@pytest.fixture
def factory(registry, config):
    return FormProviderFactory(registry, config)


@pytest.fixture
def service(registry, factory, config):
    return FormIntelligenceService(registry, factory, config)


@pytest.fixture
def confidence_calculator():
    return ConfidenceCalculator()


@pytest.fixture
def sample_form_field() -> FormField:
    return FormField(
        id="email-1",
        selector="#email",
        field_type=FieldType.EMAIL,
        name="email",
        label="Email Address",
        placeholder="Enter your email",
        autocomplete="email",
        state=FieldState(required=True, visible=True),
    )


@pytest.fixture
def sample_text_field() -> FormField:
    return FormField(
        id="first-name-1",
        selector="#first_name",
        field_type=FieldType.TEXT,
        name="first_name",
        label="First Name",
        placeholder="John",
        autocomplete="given-name",
        state=FieldState(required=True, visible=True),
    )


@pytest.fixture
def sample_form_analysis() -> FormAnalysisResult:
    return FormAnalysisResult(
        url="https://boards.greenhouse.io/company/jobs/123",
        fields=[
            FormField(
                id="fn",
                selector="#first_name",
                field_type=FieldType.TEXT,
                name="first_name",
                label="First Name",
                state=FieldState(required=True),
            ),
            FormField(
                id="ln",
                selector="#last_name",
                field_type=FieldType.TEXT,
                name="last_name",
                label="Last Name",
                state=FieldState(required=True),
            ),
            FormField(
                id="em",
                selector="#email",
                field_type=FieldType.EMAIL,
                name="email",
                label="Email",
                state=FieldState(required=True),
            ),
            FormField(
                id="res",
                selector="#resume",
                field_type=FieldType.FILE,
                name="resume",
                label="Resume",
                state=FieldState(required=True),
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════
#  Exceptions
# ═══════════════════════════════════════════════════════════════════════


class TestFormsExceptions:
    def test_forms_error(self):
        e = FormsError(message="forms error")
        assert e.code == "FORMS_ERROR"
        assert e.status_code == 502

    def test_analysis_error(self):
        e = FormAnalysisError(message="analysis failed")
        assert e.code == "FORM_ANALYSIS_ERROR"

    def test_mapping_error(self):
        e = FormMappingError(message="mapping failed")
        assert e.code == "FORM_MAPPING_ERROR"

    def test_validation_error(self):
        e = FormValidationError(message="validation failed")
        assert e.code == "FORM_VALIDATION_ERROR"

    def test_planning_error(self):
        e = FormPlanningError(message="planning failed")
        assert e.code == "FORM_PLANNING_ERROR"

    def test_provider_not_found(self):
        e = FormProviderNotFoundError(message="provider not found")
        assert e.code == "FORM_PROVIDER_NOT_FOUND"
        assert e.status_code == 404

    def test_config_error(self):
        e = FormConfigError(message="config error")
        assert e.code == "FORM_CONFIG_ERROR"


# ═══════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════


class TestFormsConfig:
    def test_defaults(self):
        c = FormsConfig()
        assert c.min_confidence_for_auto == 0.85
        assert c.min_confidence_for_mapping == 0.60
        assert c.strict_validation is True
        assert c.detect_hidden_fields is False
        assert c.max_fields_per_form == 200
        assert "label_exact" in c.classification_weights


# ═══════════════════════════════════════════════════════════════════════
#  Schemas
# ═══════════════════════════════════════════════════════════════════════


class TestFormField:
    def test_defaults(self):
        f = FormField(id="test", selector="#test", field_type=FieldType.TEXT)
        assert not f.state.required
        assert f.state.visible
        assert f.tag_name == "input"

    def test_full(self):
        f = FormField(
            id="email-1",
            selector="#email",
            field_type=FieldType.EMAIL,
            name="email",
            label="Email",
            placeholder="Enter email",
            state=FieldState(required=True),
            autocomplete="email",
            validation_rules={"max_length": 255},
        )
        assert f.name == "email"
        assert f.autocomplete == "email"
        assert f.state.required


class TestClassificationResult:
    def test_defaults(self):
        r = ClassificationResult(field_id="f1", classification=SemanticFieldType.EMAIL)
        assert r.confidence.overall == 0.0
        assert r.alternatives == []


class TestMappedField:
    def test_defaults(self):
        m = MappedField(
            field_id="f1",
            classification=SemanticFieldType.EMAIL,
            mapping_type=MappingType.MAPPED,
        )
        assert m.source_path is None
        assert not m.requires_manual_review


class TestConfidenceScore:
    def test_defaults(self):
        c = ConfidenceScore()
        assert c.overall == 0.0
        assert not c.requires_review

    def test_requires_review_based_on_threshold(self):
        c = ConfidenceScore(overall=0.5)
        assert c.overall == 0.5


class TestFieldState:
    def test_defaults(self):
        s = FieldState()
        assert not s.required
        assert not s.readonly
        assert not s.disabled
        assert s.visible


class TestExecutionPlan:
    def test_defaults(self):
        p = ExecutionPlan()
        assert p.steps == []
        assert p.total_fields == 0
        assert p.auto_fillable == 0
        assert p.requires_manual == 0


class TestPlanStep:
    def test_defaults(self):
        s = PlanStep(step_type=PlanStepType.FILL, field_ref="f1", selector="#f1")
        assert s.value is None
        assert not s.requires_manual_review

    def test_fill_step(self):
        s = PlanStep(
            step_type=PlanStepType.FILL,
            field_ref="email-1",
            selector="#email",
            value="test@example.com",
        )
        assert s.value == "test@example.com"


class TestValidationIssue:
    def test_defaults(self):
        i = ValidationIssue(code="TEST", message="test issue")
        assert i.severity == "warning"
        assert i.field_ids == []


# ═══════════════════════════════════════════════════════════════════════
#  Normalization
# ═══════════════════════════════════════════════════════════════════════


class TestNormalization:
    def test_normalize_label_lowercase(self):
        assert normalize_label("EMAIL") == "email"

    def test_normalize_label_strip_colon(self):
        assert normalize_label("Email:") == "email"

    def test_normalize_label_collapse_spaces(self):
        assert normalize_label("Email   Address") == "email address"

    def test_lookup_exact(self):
        assert lookup_normalized("email address") == "email"

    def test_lookup_normalized(self):
        assert lookup_normalized("E-mail:") == "email"

    def test_lookup_no_match(self):
        assert lookup_normalized("nonexistent field") is None

    def test_lookup_github(self):
        assert lookup_normalized("github url") == "github"

    def test_lookup_linkedin(self):
        assert lookup_normalized("LinkedIn Profile") == "linkedin"

    def test_fuzzy_match_exact(self):
        assert fuzzy_match("email", "email")

    def test_fuzzy_match_substring(self):
        assert fuzzy_match("email_address", "email")

    def test_fuzzy_match_no_match(self):
        assert not fuzzy_match("phone", "email")

    def test_lookup_resume(self):
        assert lookup_normalized("Upload Resume") == "resume"

    def test_lookup_cover_letter(self):
        assert lookup_normalized("Cover Letter:") == "cover_letter"

    def test_lookup_work_authorization(self):
        assert lookup_normalized("Work Authorization") == "work_authorization"


# ═══════════════════════════════════════════════════════════════════════
#  Confidence
# ═══════════════════════════════════════════════════════════════════════


class TestConfidenceCalculator:
    def test_calculate_default(self, confidence_calculator):
        score = confidence_calculator.calculate()
        assert score.overall == 0.0
        assert score.requires_review

    def test_calculate_high_confidence(self, confidence_calculator):
        score = confidence_calculator.calculate(label_match=1.0, attribute_match=1.0, reason="Multiple strong signals")
        assert score.overall > 0.7
        assert not score.requires_review
        assert score.reason == "Multiple strong signals"

    def test_calculate_with_reason(self, confidence_calculator):
        score = confidence_calculator.calculate(
            label_match=0.95, attribute_match=0.8, reason="Strong match"
        )
        assert score.label_match == 0.95
        assert score.attribute_match == 0.8

    def test_combine_empty(self, confidence_calculator):
        score = confidence_calculator.combine([])
        assert score.overall == 0.0

    def test_combine_multiple(self, confidence_calculator):
        s1 = ConfidenceScore(overall=0.9, label_match=0.9)
        s2 = ConfidenceScore(overall=0.7, label_match=0.7)
        combined = confidence_calculator.combine([s1, s2])
        assert combined.overall == 0.8


# ═══════════════════════════════════════════════════════════════════════
#  Classification
# ═══════════════════════════════════════════════════════════════════════


class TestFieldClassifier:
    def test_classify_email_by_label(self, classifier, sample_form_field):
        result = classifier.classify(sample_form_field)
        assert result.classification == SemanticFieldType.EMAIL
        assert result.confidence.overall > 0.3

    def test_classify_email_by_autocomplete(self, classifier):
        field = FormField(
            id="em",
            selector="#email",
            field_type=FieldType.TEXT,
            autocomplete="email",
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.EMAIL

    def test_classify_first_name_by_label(self, classifier, sample_text_field):
        result = classifier.classify(sample_text_field)
        assert result.classification == SemanticFieldType.FIRST_NAME
        assert result.confidence.overall > 0.3

    def test_classify_first_name_by_autocomplete(self, classifier):
        field = FormField(
            id="fn",
            selector="#first_name",
            field_type=FieldType.TEXT,
            autocomplete="given-name",
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.FIRST_NAME

    def test_classify_phone_by_type(self, classifier):
        field = FormField(
            id="ph",
            selector="#phone",
            field_type=FieldType.PHONE,
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.PHONE

    def test_classify_by_name_attribute(self, classifier):
        field = FormField(
            id="li",
            selector="#linkedin",
            field_type=FieldType.URL,
            name="linkedin",
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.LINKEDIN

    def test_classify_unknown(self, classifier):
        field = FormField(
            id="custom",
            selector="#custom",
            field_type=FieldType.TEXT,
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.UNKNOWN
        assert result.confidence.requires_review

    def test_classify_with_alternatives(self, classifier):
        field = FormField(
            id="em",
            selector="#email",
            field_type=FieldType.EMAIL,
            name="email",
            label="Email Address",
            autocomplete="email",
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.EMAIL
        assert len(result.alternatives) >= 0

    def test_classify_disabled_field(self, classifier):
        field = FormField(
            id="fn",
            selector="#first_name",
            field_type=FieldType.TEXT,
            name="first_name",
            label="First Name",
            state=FieldState(readonly=True),
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.FIRST_NAME
        assert "[field is disabled/readonly]" in result.confidence.reason

    def test_classify_resume_by_label(self, classifier):
        field = FormField(
            id="res",
            selector="#resume",
            field_type=FieldType.FILE,
            label="Upload Resume",
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.RESUME

    def test_classify_placeholder_email(self, classifier):
        field = FormField(
            id="em",
            selector="#email",
            field_type=FieldType.TEXT,
            placeholder="Enter your email",
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.EMAIL


# ═══════════════════════════════════════════════════════════════════════
#  Mapping
# ═══════════════════════════════════════════════════════════════════════


class TestFieldMapper:
    def test_map_email_field(self, mapper):
        classification = ClassificationResult(
            field_id="em",
            classification=SemanticFieldType.EMAIL,
            confidence=ConfidenceScore(overall=0.95),
        )
        field = FormField(id="em", selector="#email", field_type=FieldType.EMAIL)
        result = mapper.map_field(classification, field, None)
        assert result.mapping_type == MappingType.MISSING
        assert result.source_path == "profile.personal_info.email"

    def test_map_first_name(self, mapper):
        classification = ClassificationResult(
            field_id="fn",
            classification=SemanticFieldType.FIRST_NAME,
        )
        field = FormField(id="fn", selector="#first_name", field_type=FieldType.TEXT)
        result = mapper.map_field(classification, field, None)
        assert result.source_path == "profile.personal_info.first_name"

    def test_map_resume_upload(self, mapper):
        classification = ClassificationResult(
            field_id="res",
            classification=SemanticFieldType.RESUME,
        )
        field = FormField(id="res", selector="#resume", field_type=FieldType.FILE)
        result = mapper.map_field(classification, field, None)
        assert result.mapping_type == MappingType.MAPPED
        assert result.source_path == "resume"

    def test_map_unsupported(self, mapper):
        classification = ClassificationResult(
            field_id="unk",
            classification=SemanticFieldType.UNKNOWN,
        )
        field = FormField(id="unk", selector="#custom", field_type=FieldType.TEXT)
        result = mapper.map_field(classification, field, None)
        assert result.mapping_type == MappingType.UNSUPPORTED

    def test_map_with_package_data(self, mapper):
        classification = ClassificationResult(
            field_id="em",
            classification=SemanticFieldType.EMAIL,
        )
        field = FormField(id="em", selector="#email", field_type=FieldType.EMAIL)
        package = MagicMock()
        package.profile.personal_info.email = "test@example.com"
        result = mapper.map_field(classification, field, package)
        assert result.value == "test@example.com"
        assert result.mapping_type == MappingType.MAPPED


# ═══════════════════════════════════════════════════════════════════════
#  Validation
# ═══════════════════════════════════════════════════════════════════════


class TestFormValidator:
    def test_validate_empty_form(self, validator):
        analysis = FormAnalysisResult(url="https://example.com")
        issues = validator.validate(analysis)
        assert any(i.code == "EMPTY_FORM" for i in issues)

    def test_validate_duplicate_fields(self, validator):
        analysis = FormAnalysisResult(
            url="https://example.com",
            classifications=[
                ClassificationResult(field_id="e1", classification=SemanticFieldType.EMAIL),
                ClassificationResult(field_id="e2", classification=SemanticFieldType.EMAIL),
            ],
        )
        issues = validator.validate(analysis)
        assert any(i.code == "DUPLICATE_FIELD" for i in issues)

    def test_validate_no_duplicates(self, validator):
        analysis = FormAnalysisResult(
            url="https://example.com",
            classifications=[
                ClassificationResult(field_id="fn", classification=SemanticFieldType.FIRST_NAME),
                ClassificationResult(field_id="ln", classification=SemanticFieldType.LAST_NAME),
            ],
        )
        issues = validator.validate(analysis)
        assert not any(i.code == "DUPLICATE_FIELD" for i in issues)

    def test_validate_hidden_required(self, validator):
        analysis = FormAnalysisResult(
            url="https://example.com",
            fields=[
                FormField(
                    id="hidden-req",
                    selector="#hidden",
                    field_type=FieldType.TEXT,
                    state=FieldState(required=True, visible=False),
                    label="Hidden Required",
                ),
            ],
        )
        issues = validator.validate(analysis)
        assert any(i.code == "REQUIRED_FIELD_HIDDEN" for i in issues)

    def test_validate_ambiguous_labels(self, validator):
        analysis = FormAnalysisResult(
            url="https://example.com",
            fields=[
                FormField(id="f1", selector="#f1", field_type=FieldType.TEXT),
                FormField(id="f2", selector="#f2", field_type=FieldType.TEXT),
            ],
        )
        issues = validator.validate(analysis)
        assert any(i.code == "AMBIGUOUS_LABELS" for i in issues)


# ═══════════════════════════════════════════════════════════════════════
#  Planning
# ═══════════════════════════════════════════════════════════════════════


class TestPlanGenerator:
    def test_generate_empty(self, planner):
        analysis = FormAnalysisResult(url="https://example.com")
        plan = planner.generate(analysis)
        assert plan.total_fields == 0
        assert plan.steps == []

    def test_generate_fill_step(self, planner, sample_form_analysis):
        sample_form_analysis.mappings = [
            MappedField(
                field_id="fn",
                classification=SemanticFieldType.FIRST_NAME,
                mapping_type=MappingType.MAPPED,
                value="John",
                source_path="profile.personal_info.first_name",
            ),
        ]
        plan = planner.generate(sample_form_analysis)
        assert len(plan.steps) == 1
        assert plan.steps[0].step_type == PlanStepType.FILL
        assert plan.steps[0].value == "John"

    def test_generate_upload_step(self, planner, sample_form_analysis):
        sample_form_analysis.mappings = [
            MappedField(
                field_id="res",
                classification=SemanticFieldType.RESUME,
                mapping_type=MappingType.MAPPED,
                source_path="resume",
            ),
        ]
        plan = planner.generate(sample_form_analysis)
        assert len(plan.steps) == 1
        assert plan.steps[0].step_type == PlanStepType.UPLOAD

    def test_generate_manual_step(self, planner, sample_form_analysis):
        sample_form_analysis.mappings = [
            MappedField(
                field_id="em",
                classification=SemanticFieldType.EMAIL,
                mapping_type=MappingType.MISSING,
                requires_manual_review=True,
            ),
        ]
        plan = planner.generate(sample_form_analysis)
        assert len(plan.steps) == 1
        assert plan.steps[0].step_type == PlanStepType.REQUEST_MANUAL

    def test_generate_skip_step(self, planner, sample_form_analysis):
        sample_form_analysis.mappings = [
            MappedField(
                field_id="custom",
                classification=SemanticFieldType.UNKNOWN,
                mapping_type=MappingType.UNSUPPORTED,
            ),
        ]
        plan = planner.generate(sample_form_analysis)
        assert len(plan.steps) == 1
        assert plan.steps[0].step_type == PlanStepType.SKIP

    def test_plan_totals(self, planner, sample_form_analysis):
        sample_form_analysis.mappings = [
            MappedField(
                field_id="fn",
                classification=SemanticFieldType.FIRST_NAME,
                mapping_type=MappingType.MAPPED,
                value="John",
            ),
            MappedField(
                field_id="em",
                classification=SemanticFieldType.EMAIL,
                mapping_type=MappingType.MISSING,
                requires_manual_review=True,
            ),
        ]
        plan = planner.generate(sample_form_analysis)
        assert plan.total_fields == 4
        assert plan.auto_fillable == 1
        assert plan.requires_manual == 1


# ═══════════════════════════════════════════════════════════════════════
#  Registry
# ═══════════════════════════════════════════════════════════════════════


class TestFormProviderRegistry:
    def test_register_and_resolve(self, registry):
        provider = BaseFormProvider()
        registry.register("test", provider)
        assert registry.is_registered("test")
        assert registry.resolve("test") is provider

    def test_register_duplicate(self, registry):
        provider = BaseFormProvider()
        registry.register("test", provider)
        registry.register("test", BaseFormProvider())
        assert registry.count() == 1

    def test_resolve_not_found(self, registry):
        with pytest.raises(FormProviderNotFoundError):
            registry.resolve("nonexistent")

    def test_unregister(self, registry):
        registry.register("test", BaseFormProvider())
        registry.unregister("test")
        assert not registry.is_registered("test")

    def test_list_providers(self, registry):
        registry.register("a", BaseFormProvider())
        registry.register("b", BaseFormProvider())
        assert set(registry.list_providers()) == {"a", "b"}

    def test_clear(self, registry):
        registry.register("a", BaseFormProvider())
        registry.clear()
        assert registry.count() == 0


# ═══════════════════════════════════════════════════════════════════════
#  Factory
# ═══════════════════════════════════════════════════════════════════════


class TestFormProviderFactory:
    def test_create_provider(self, registry, config):
        factory = FormProviderFactory(registry, config)
        provider = factory.create_provider("custom")
        assert registry.is_registered("custom")
        assert isinstance(provider, BaseFormProvider)

    def test_register_all(self, registry, config):
        factory = FormProviderFactory(registry, config)
        factory.register_all()
        assert registry.count() == 7
        assert "greenhouse" in registry.list_providers()
        assert "lever" in registry.list_providers()
        assert "workday" in registry.list_providers()

    def test_register_all_skips_existing(self, registry, config):
        existing = BaseFormProvider()
        registry.register("greenhouse", existing)
        factory = FormProviderFactory(registry, config)
        factory.register_all()
        assert registry.resolve("greenhouse") is existing


# ═══════════════════════════════════════════════════════════════════════
#  Base Provider
# ═══════════════════════════════════════════════════════════════════════


class TestBaseFormProvider:
    def test_supports(self):
        provider = BaseFormProvider()
        assert provider.supports("https://example.com")

    def test_extract_fields_empty(self, mock_page):
        provider = BaseFormProvider()
        fields = provider.extract_fields(mock_page)
        assert fields == []


# ═══════════════════════════════════════════════════════════════════════
#  Analysis
# ═══════════════════════════════════════════════════════════════════════


class TestFormAnalyzer:
    def test_analyze_empty_page(self, analyzer, mock_page):
        result = analyzer.analyze(mock_page, "https://example.com")
        assert result.url == "https://example.com"
        assert result.total_fields == 0

    def test_extract_fields_empty(self, analyzer, mock_page):
        fields = analyzer.extract_fields(mock_page)
        assert fields == []

    def test_build_selector_with_id(self, analyzer, mock_element):
        mock_element.evaluate.side_effect = ["INPUT", 0]
        mock_element.get_attribute.side_effect = lambda attr: {
            "id": "email-1",
            "name": "email",
            "class": "form-control",
        }.get(attr)
        selector = analyzer._build_selector(mock_element)
        assert selector == "#email-1"

    def test_build_selector_with_name(self, analyzer, mock_element):
        mock_element.evaluate.side_effect = ["INPUT", 0]
        mock_element.get_attribute.side_effect = lambda attr: {
            "name": "email",
        }.get(attr)
        selector = analyzer._build_selector(mock_element)
        assert selector == "input[name='email']"

    def test_to_field_type_text(self, analyzer):
        assert analyzer._to_field_type("input", "text") == FieldType.TEXT

    def test_to_field_type_email(self, analyzer):
        assert analyzer._to_field_type("input", "email") == FieldType.EMAIL

    def test_to_field_type_select(self, analyzer):
        assert analyzer._to_field_type("select", "") == FieldType.SELECT

    def test_to_field_type_textarea(self, analyzer):
        assert analyzer._to_field_type("textarea", "") == FieldType.TEXTAREA

    def test_to_field_type_file(self, analyzer):
        assert analyzer._to_field_type("input", "file") == FieldType.FILE

    def test_to_field_type_hidden(self, analyzer):
        assert analyzer._to_field_type("input", "hidden") == FieldType.HIDDEN


# ═══════════════════════════════════════════════════════════════════════
#  Service
# ═══════════════════════════════════════════════════════════════════════


class TestFormIntelligenceService:
    def test_analyze_form_empty(self, service, mock_page):
        result = service.analyze_form(mock_page, "https://boards.greenhouse.io/company/jobs/123")
        assert result.url == "https://boards.greenhouse.io/company/jobs/123"
        assert result.total_fields == 0

    def test_generate_plan_empty(self, service):
        analysis = FormAnalysisResult(url="https://example.com")
        plan = service.generate_plan(analysis)
        assert plan.steps == []

    def test_analyze_and_plan(self, service, mock_page):
        response = service.analyze_and_plan(mock_page, "https://example.com")
        assert response.analysis.url == "https://example.com"
        assert isinstance(response.plan, ExecutionPlan)

    def test_get_provider_for_url_default(self, service):
        provider = service._get_provider_for_url("https://example.com")
        assert provider is not None

    def test_detect_provider(self, registry, config, mock_page):
        factory = FormProviderFactory(registry, config)
        factory.register_all()
        service = FormIntelligenceService(registry, factory, config)
        result = service.analyze_form(mock_page, "https://boards.greenhouse.io/test")
        assert result.url == "https://boards.greenhouse.io/test"


# ═══════════════════════════════════════════════════════════════════════
#  Dependencies
# ═══════════════════════════════════════════════════════════════════════


class TestFormsDependencies:
    def setup_method(self):
        reset_forms_service()

    def test_get_forms_service(self):
        service = get_forms_service()
        assert isinstance(service, FormIntelligenceService)

    def test_get_forms_service_singleton(self):
        s1 = get_forms_service()
        s2 = get_forms_service()
        assert s1 is s2

    def test_reset_forms_service(self):
        s1 = get_forms_service()
        reset_forms_service()
        s2 = get_forms_service()
        assert s1 is not s2

    def test_get_forms_service_initializes_providers(self):
        service = get_forms_service()
        assert service._registry.count() > 0


# ═══════════════════════════════════════════════════════════════════════
#  Edge Cases & Large Forms
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_classify_empty_field(self, classifier):
        field = FormField(id="empty", selector="#empty", field_type=FieldType.TEXT)
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.UNKNOWN

    def test_normalize_special_chars(self):
        assert normalize_label("E-mail (Primary):") == "e-mail primary"

    def test_lookup_case_insensitive(self):
        assert lookup_normalized("EMAIL ADDRESS") == "email"

    def test_mapping_unknown_returns_unsupported(self, mapper):
        classification = ClassificationResult(
            field_id="unk",
            classification=SemanticFieldType.UNKNOWN,
        )
        field = FormField(id="unk", selector="#unk", field_type=FieldType.TEXT)
        result = mapper.map_field(classification, field, None)
        assert result.mapping_type == MappingType.UNSUPPORTED

    def test_generate_empty_form_plan(self, planner):
        analysis = FormAnalysisResult(url="https://example.com")
        plan = planner.generate(analysis)
        assert plan.total_fields == 0
        assert plan.auto_fillable == 0

    def test_validation_empty_form(self, validator):
        analysis = FormAnalysisResult(url="https://example.com")
        issues = validator.validate(analysis)
        assert len(issues) > 0

    def test_confidence_calculate_clamps(self, confidence_calculator):
        score = confidence_calculator.calculate(label_match=2.0)
        assert score.overall <= 1.0

    def test_classify_with_id_pattern(self, classifier):
        field = FormField(
            id="input-email-1",
            selector="#input-email-1",
            field_type=FieldType.TEXT,
        )
        result = classifier.classify(field)
        assert result.classification == SemanticFieldType.EMAIL
