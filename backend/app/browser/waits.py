from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.browser.exceptions import ElementNotFoundError, TimeoutError


class WaitStrategy:
    def __init__(self, timeout_ms: float = 10000.0) -> None:
        self._timeout_ms = timeout_ms

    def wait_for_selector(self, page: Any, selector: str) -> Any:
        try:
            return page.wait_for_selector(
                selector,
                timeout=self._timeout_ms,
                state="visible",
            )
        except Exception as e:
            raise ElementNotFoundError(message=f"Element '{selector}' not visible within {self._timeout_ms}ms.") from e

    def wait_for_element_state(self, page: Any, selector: str, state: str = "visible") -> Any:
        try:
            element = page.locator(selector)
            element.wait_for(state=state, timeout=self._timeout_ms)
            return element
        except Exception as e:
            raise ElementNotFoundError(
                message=f"Element '{selector}' not in state '{state}' within {self._timeout_ms}ms."
            ) from e

    def wait_for_network_idle(self, page: Any) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=self._timeout_ms)
        except Exception as e:
            raise TimeoutError(message=f"Network did not become idle within {self._timeout_ms}ms.") from e

    def wait_for_load_state(self, page: Any, state: str = "load") -> None:
        try:
            page.wait_for_load_state(state, timeout=self._timeout_ms)
        except Exception as e:
            raise TimeoutError(message=f"Page did not reach load state '{state}' within {self._timeout_ms}ms.") from e

    def wait_for_function(self, page: Any, fn: str) -> Any:
        try:
            return page.wait_for_function(fn, timeout=self._timeout_ms)
        except Exception as e:
            raise TimeoutError(message=f"Function did not return true within {self._timeout_ms}ms.") from e

    def wait_for_url(self, page: Any, url_pattern: str) -> None:
        try:
            page.wait_for_url(url_pattern, timeout=self._timeout_ms)
        except Exception as e:
            raise TimeoutError(message=f"URL did not match '{url_pattern}' within {self._timeout_ms}ms.") from e

    def wait_for_timeout(self, page: Any, duration_ms: float) -> None:
        page.wait_for_timeout(duration_ms)

    def retry(self, action: Callable[[], Any], attempts: int = 3) -> Any:
        last_exception: Exception | None = None
        for attempt in range(attempts):
            try:
                return action()
            except Exception as e:
                last_exception = e
                if attempt < attempts - 1:
                    import time as _time

                    _time.sleep(0.5)
        raise last_exception  # type: ignore[misc]
