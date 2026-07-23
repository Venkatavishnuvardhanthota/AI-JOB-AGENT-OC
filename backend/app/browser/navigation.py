from __future__ import annotations

import time
from typing import Any

from app.browser.exceptions import ElementNotFoundError
from app.browser.schemas import NavigationResult
from app.browser.waits import WaitStrategy


class NavigationHelper:
    def __init__(self, waits: WaitStrategy) -> None:
        self._waits = waits

    def goto(
        self,
        page: Any,
        url: str,
        timeout_ms: float = 60000.0,
        wait_until: str = "load",
    ) -> NavigationResult:
        start = time.monotonic()
        try:
            response = page.goto(url, timeout=timeout_ms, wait_until=wait_until)
            duration = (time.monotonic() - start) * 1000
            status_code = response.status if response else None
            title = page.title() if page else None
            return NavigationResult(
                success=True,
                url=page.url if page else url,
                status_code=status_code,
                title=title,
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return NavigationResult(
                success=False,
                url=url,
                duration_ms=round(duration, 2),
                error=str(e),
            )

    def reload(self, page: Any, timeout_ms: float = 60000.0) -> NavigationResult:
        start = time.monotonic()
        try:
            response = page.reload(timeout=timeout_ms)
            duration = (time.monotonic() - start) * 1000
            status_code = response.status if response else None
            return NavigationResult(
                success=True,
                url=page.url if page else "",
                status_code=status_code,
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return NavigationResult(
                success=False,
                url=page.url if page else "",
                duration_ms=round(duration, 2),
                error=str(e),
            )

    def back(self, page: Any, timeout_ms: float = 60000.0) -> NavigationResult:
        start = time.monotonic()
        try:
            page.go_back(timeout=timeout_ms)
            duration = (time.monotonic() - start) * 1000
            return NavigationResult(
                success=True,
                url=page.url if page else "",
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return NavigationResult(
                success=False,
                url=page.url if page else "",
                duration_ms=round(duration, 2),
                error=str(e),
            )

    def forward(self, page: Any, timeout_ms: float = 60000.0) -> NavigationResult:
        start = time.monotonic()
        try:
            page.go_forward(timeout=timeout_ms)
            duration = (time.monotonic() - start) * 1000
            return NavigationResult(
                success=True,
                url=page.url if page else "",
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return NavigationResult(
                success=False,
                url=page.url if page else "",
                duration_ms=round(duration, 2),
                error=str(e),
            )

    def wait_for_network_idle(self, page: Any, timeout_ms: float | None = None) -> None:
        self._waits.wait_for_network_idle(page)

    def safe_click(self, page: Any, selector: str, timeout_ms: float = 10000.0) -> None:
        try:
            self._waits.wait_for_element_state(page, selector, "visible")
            page.click(selector, timeout=timeout_ms)
        except Exception as e:
            raise ElementNotFoundError(message=f"Failed to safely click '{selector}'.") from e

    def safe_fill(self, page: Any, selector: str, value: str, timeout_ms: float = 10000.0) -> None:
        try:
            self._waits.wait_for_element_state(page, selector, "visible")
            page.fill(selector, value, timeout=timeout_ms)
        except Exception as e:
            raise ElementNotFoundError(message=f"Failed to safely fill '{selector}'.") from e

    def safe_select(self, page: Any, selector: str, value: str, timeout_ms: float = 10000.0) -> None:
        try:
            self._waits.wait_for_element_state(page, selector, "visible")
            page.select_option(selector, value, timeout=timeout_ms)
        except Exception as e:
            raise ElementNotFoundError(message=f"Failed to safely select '{value}' in '{selector}'.") from e
