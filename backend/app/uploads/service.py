from __future__ import annotations

from typing import Any

import structlog

from app.browser.service import BrowserService
from app.uploads.capabilities import UploadCapabilityAnalyzer
from app.uploads.config import UploadsConfig
from app.uploads.factory import UploadProviderFactory
from app.uploads.manager import UploadManager
from app.uploads.registry import UploadProviderRegistry
from app.uploads.schemas import (
    DocumentType,
    ProviderCapabilities,
    UploadPlan,
    UploadResult,
    UploadSummary,
)
from app.uploads.validator import DocumentValidator

logger = structlog.get_logger(__name__)


class DocumentUploadService:
    def __init__(
        self,
        registry: UploadProviderRegistry,
        factory: UploadProviderFactory,
        config: UploadsConfig | None = None,
        browser_service: BrowserService | None = None,
    ) -> None:
        self._registry = registry
        self._factory = factory
        self._config = config or UploadsConfig()
        self._logger = logger.bind(service="document_upload")

        self._validator = DocumentValidator(self._config)
        self._capability_analyzer = UploadCapabilityAnalyzer()
        self._manager = UploadManager(
            validator=self._validator,
            capability_analyzer=self._capability_analyzer,
            browser_service=browser_service,
        )

    def create_upload_plan(self, execution_plan: Any, application_package: Any | None = None) -> UploadPlan:
        return self._manager.create_plan(execution_plan, application_package)

    def execute_upload_plan(self, page: Any, plan: UploadPlan) -> list[UploadResult]:
        return self._manager.execute_plan(page, plan)

    def execute_and_summarize(self, page: Any, plan: UploadPlan) -> tuple[list[UploadResult], UploadSummary]:
        results = self.execute_upload_plan(page, plan)
        summary = self._manager.summarize(results)
        return results, summary

    def validate_document(self, file_path: str, document_type: DocumentType) -> list[str]:
        return self._validator.validate_file(file_path, document_type)

    def validate_and_raise(self, file_path: str, document_type: DocumentType) -> None:
        self._validator.validate_file_upload(file_path, document_type)

    def analyze_upload_field(self, page: Any, selector: str) -> Any:
        return self._capability_analyzer.analyze(page, selector)

    def get_provider_capabilities(self, provider_name: str) -> ProviderCapabilities:
        return self._capability_analyzer.get_provider_capabilities(provider_name)

    def get_provider_for_url(self, url: str) -> Any:
        provider = self._factory.detect_provider(url)
        if provider is None:
            if self._registry.is_registered("default"):
                return self._registry.resolve("default")
            default = self._factory.create_provider("default")
            return default
        return provider

    def detect_provider(self, url: str) -> str | None:
        provider = self.get_provider_for_url(url)
        if provider is None:
            return None
        return getattr(provider, "name", "default")
