from __future__ import annotations

from app.uploads.interfaces import UploadProvider
from app.uploads.schemas import ProviderCapabilities


class BaseUploadProvider(UploadProvider):
    def __init__(self, name: str = "default") -> None:
        self._name = name

    def supports(self, url: str) -> bool:
        return True

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name=self._name,
            max_file_size_mb=10.0,
        )

    @property
    def name(self) -> str:
        return self._name
