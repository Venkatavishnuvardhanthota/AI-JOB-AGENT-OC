from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from app.browser.exceptions import ScreenshotError
from app.browser.schemas import ScreenshotOptions


class ScreenshotManager:
    def __init__(self, screenshot_path: str = "screenshots", max_files: int = 100) -> None:
        self._screenshot_path = screenshot_path
        self._max_files = max_files
        os.makedirs(self._screenshot_path, exist_ok=True)

    def take_screenshot(
        self,
        page: Any,
        name: str | None = None,
        options: ScreenshotOptions | None = None,
    ) -> str:
        opts = options or ScreenshotOptions()
        filename = self._generate_filename(name, opts.type)
        file_path = os.path.join(self._screenshot_path, filename)
        try:
            page.screenshot(
                path=file_path,
                full_page=opts.full_page,
                quality=opts.quality,
                type=opts.type,
                timeout=opts.timeout_ms,
            )
            self._cleanup_old_files()
            return file_path
        except Exception as e:
            raise ScreenshotError(message=f"Failed to capture screenshot: {e!s}") from e

    def take_element_screenshot(
        self,
        page: Any,
        selector: str,
        name: str | None = None,
    ) -> str:
        filename = self._generate_filename(name or f"element_{selector}", "png")
        file_path = os.path.join(self._screenshot_path, filename)
        try:
            element = page.locator(selector)
            element.screenshot(path=file_path)
            return file_path
        except Exception as e:
            raise ScreenshotError(message=f"Failed to capture element screenshot '{selector}': {e!s}") from e

    def take_failure_screenshot(
        self,
        page: Any,
        error_context: str = "failure",
    ) -> str:
        return self.take_screenshot(
            page,
            name=f"failure_{error_context}",
            options=ScreenshotOptions(full_page=True),
        )

    def _generate_filename(self, name: str | None, ext: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        base = name or "screenshot"
        safe_base = "".join(c if c.isalnum() or c in "_-" else "_" for c in base)
        return f"{timestamp}_{safe_base}.{ext}"

    def _cleanup_old_files(self) -> None:
        try:
            files = sorted(
                [
                    f
                    for f in os.listdir(self._screenshot_path)
                    if os.path.isfile(os.path.join(self._screenshot_path, f))
                ],
                key=lambda f: os.path.getmtime(os.path.join(self._screenshot_path, f)),
            )
            while len(files) > self._max_files:
                oldest = files.pop(0)
                os.remove(os.path.join(self._screenshot_path, oldest))
        except Exception:
            pass
