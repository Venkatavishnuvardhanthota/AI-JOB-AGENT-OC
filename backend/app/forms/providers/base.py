from __future__ import annotations

from typing import Any

from app.forms.analysis import FormAnalyzer
from app.forms.interfaces import FormAnalyzer as FormAnalyzerInterface
from app.forms.schemas import FormAnalysisResult, FormField


class BaseFormProvider(FormAnalyzerInterface):
    def __init__(self, analyzer: FormAnalyzer | None = None) -> None:
        self._analyzer = analyzer or FormAnalyzer()

    def analyze(self, page: Any, url: str) -> FormAnalysisResult:
        return self._analyzer.analyze(page, url)

    def extract_fields(self, page: Any) -> list[FormField]:
        return self._analyzer.extract_fields(page)

    def supports(self, url: str) -> bool:
        return True
