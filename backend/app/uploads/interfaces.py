from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.uploads.schemas import (
    ProviderCapabilities,
    UploadPlan,
    UploadResult,
    VerificationResult,
)


class UploadProvider(ABC):
    @abstractmethod
    def supports(self, url: str) -> bool: ...

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities: ...


class DocumentUploader(ABC):
    @abstractmethod
    def upload(self, page: Any, selector: str, file_path: str, timeout_ms: float) -> None: ...

    @abstractmethod
    def upload_multiple(self, page: Any, selector: str, file_paths: list[str], timeout_ms: float) -> None: ...


class UploadPlanner(ABC):
    @abstractmethod
    def plan(self, execution_plan: Any, application_package: Any | None = None) -> UploadPlan: ...


class UploadExecutor(ABC):
    @abstractmethod
    def execute(self, page: Any, plan: UploadPlan) -> list[UploadResult]: ...

    @abstractmethod
    def execute_task(self, page: Any, task: Any) -> UploadResult: ...


class UploadVerifier(ABC):
    @abstractmethod
    def verify(self, page: Any, task: Any) -> VerificationResult: ...


class UploadValidator(ABC):
    @abstractmethod
    def validate_file(self, file_path: str, document_type: Any) -> list[Any]: ...

    @abstractmethod
    def validate_plan(self, plan: UploadPlan) -> list[Any]: ...


class CapabilityAnalyzer(ABC):
    @abstractmethod
    def analyze(self, page: Any, selector: str) -> Any: ...

    @abstractmethod
    def get_provider_capabilities(self, provider_name: str) -> ProviderCapabilities: ...
