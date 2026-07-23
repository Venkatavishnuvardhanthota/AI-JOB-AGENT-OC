from __future__ import annotations

from functools import lru_cache

from app.application_package.config import PackageConfig
from app.application_package.service import ApplicationPackageService


@lru_cache
def _get_config() -> PackageConfig:
    return PackageConfig()


@lru_cache
def get_application_package_service() -> ApplicationPackageService:
    return ApplicationPackageService(config=_get_config())
