from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.forms.schemas import FormAnalysisResult, FormField


class FormAnalyzer(ABC):
    @abstractmethod
    def analyze(self, page: Any, url: str) -> FormAnalysisResult: ...

    @abstractmethod
    def extract_fields(self, page: Any) -> list[FormField]: ...

    @abstractmethod
    def supports(self, url: str) -> bool: ...


class FormClassifier(ABC):
    @abstractmethod
    def classify(self, field: FormField, context: list[FormField] | None = None) -> Any: ...


class FieldMapper(ABC):
    @abstractmethod
    def map_field(self, classification: Any, field: Any, application_package: Any) -> Any: ...


class PlanGenerator(ABC):
    @abstractmethod
    def generate(self, analysis: FormAnalysisResult, application_package: Any) -> Any: ...


class FormValidator(ABC):
    @abstractmethod
    def validate(self, analysis: FormAnalysisResult) -> list[Any]: ...
