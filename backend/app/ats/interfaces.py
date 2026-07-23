from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.ats.schemas import (
    ATSApplicationRequest,
    ATSApplicationResult,
    ATSDetectionResult,
    ATSJobInfo,
    ATSJobSearchRequest,
    ATSLoginRequest,
    ATSLoginResult,
    ATSNavigationRequest,
    ATSNavigationResult,
    ATSProviderCapability,
    ATSProviderMetadata,
    ATSValidationResult,
)
from app.browser.service import BrowserService


class ATSProvider(ABC):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"
    homepage_url: str = ""
    requires_auth: bool = False
    requires_login: bool = False

    def __init__(self, browser: BrowserService, config: Any | None = None) -> None:
        self.browser = browser
        self.config = config

    @abstractmethod
    def supports(self, url: str) -> bool: ...

    @abstractmethod
    def detect(self, url: str) -> ATSDetectionResult | None: ...

    @abstractmethod
    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult: ...

    @abstractmethod
    def navigate(self, page: Any, request: ATSNavigationRequest) -> ATSNavigationResult: ...

    @abstractmethod
    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]: ...

    @abstractmethod
    def open_application(self, page: Any, request: ATSApplicationRequest) -> ATSApplicationResult: ...

    @abstractmethod
    def validate(self, page: Any) -> ATSValidationResult: ...

    @abstractmethod
    def capabilities(self) -> list[ATSProviderCapability]: ...

    @abstractmethod
    def metadata(self) -> ATSProviderMetadata: ...
