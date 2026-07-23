from __future__ import annotations

from typing import Any

from app.browser.exceptions import StorageError


class StorageManager:
    @staticmethod
    def get_storage_state(context: Any) -> dict[str, Any]:
        try:
            return context.storage_state()
        except Exception as e:
            raise StorageError(message=f"Failed to get storage state: {e!s}") from e

    @staticmethod
    def add_init_script(context: Any, script: str) -> None:
        try:
            context.add_init_script(script)
        except Exception as e:
            raise StorageError(message=f"Failed to add init script: {e!s}") from e

    @staticmethod
    def set_extra_http_headers(context: Any, headers: dict[str, str]) -> None:
        try:
            context.set_extra_http_headers(headers)
        except Exception as e:
            raise StorageError(message=f"Failed to set extra HTTP headers: {e!s}") from e

    @staticmethod
    def grant_permissions(context: Any, permissions: list[str]) -> None:
        try:
            context.grant_permissions(permissions)
        except Exception as e:
            raise StorageError(message=f"Failed to grant permissions: {e!s}") from e

    @staticmethod
    def clear_permissions(context: Any) -> None:
        try:
            context.clear_permissions()
        except Exception as e:
            raise StorageError(message=f"Failed to clear permissions: {e!s}") from e

    @staticmethod
    def set_geolocation(context: Any, latitude: float, longitude: float) -> None:
        try:
            context.set_geolocation({"latitude": latitude, "longitude": longitude})
        except Exception as e:
            raise StorageError(message=f"Failed to set geolocation: {e!s}") from e

    @staticmethod
    def set_offline(context: Any, offline: bool) -> None:
        try:
            context.set_offline(offline)
        except Exception as e:
            raise StorageError(message=f"Failed to set offline mode: {e!s}") from e
