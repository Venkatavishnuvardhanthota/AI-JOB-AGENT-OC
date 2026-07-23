from __future__ import annotations

from typing import Any

import structlog

from app.uploads.interfaces import CapabilityAnalyzer
from app.uploads.schemas import ProviderCapabilities, UploadFieldInfo

logger = structlog.get_logger(__name__)


class UploadCapabilityAnalyzer(CapabilityAnalyzer):
    def __init__(self) -> None:
        self._logger = logger.bind(service="capability_analyzer")

    def analyze(self, page: Any, selector: str) -> UploadFieldInfo:
        if page is None:
            return UploadFieldInfo(selector=selector)

        info = UploadFieldInfo(selector=selector)
        try:
            element = page.locator(selector)
            if element is None:
                return info

            accept = element.get_attribute("accept")
            if accept:
                types = []
                for part in accept.split(","):
                    part = part.strip()
                    if part.startswith("."):
                        info.accepted_extensions.append(part.lower())
                    elif "/" in part:
                        types.append(part.lower())
                info.accepted_mime_types = types

            multiple = element.get_attribute("multiple")
            info.multiple = multiple is not None

            required = element.get_attribute("required")
            info.required = required is not None

            hidden = element.get_attribute("type")
            if hidden and hidden.lower() == "hidden":
                info.native_file_input = False

        except Exception:
            self._logger.warning("Failed to analyze upload field", selector=selector)

        return info

    def get_provider_capabilities(self, provider_name: str) -> ProviderCapabilities:
        caps = ProviderCapabilities(provider_name=provider_name)

        provider_lower = provider_name.lower()

        if "greenhouse" in provider_lower:
            caps.supports_multiple_files = False
            caps.supports_drag_and_drop = False
            caps.supports_replace = False
            caps.max_file_size_mb = 10.0
            caps.limitations = ["Single file upload only", "No drag-and-drop"]
        elif "lever" in provider_lower:
            caps.supports_multiple_files = True
            caps.supports_drag_and_drop = True
            caps.supports_replace = True
            caps.max_file_size_mb = 25.0
            caps.limitations = ["Max 25MB per file"]
        elif "ashby" in provider_lower:
            caps.supports_multiple_files = False
            caps.supports_drag_and_drop = True
            caps.max_file_size_mb = 10.0
            caps.limitations = ["Single file upload only"]
        elif "workday" in provider_lower:
            caps.supports_multiple_files = True
            caps.supports_drag_and_drop = True
            caps.supports_replace = True
            caps.max_file_size_mb = 20.0
            caps.limitations = ["May require additional confirmation"]
        elif provider_lower == "default":
            caps.supports_multiple_files = False
            caps.max_file_size_mb = 10.0
            caps.limitations = ["Default provider limitations"]

        return caps
