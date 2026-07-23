from __future__ import annotations

from typing import Any

from app.browser.exceptions import ElementNotFoundError, InvalidSelectorError


class SelectorHelper:
    @staticmethod
    def by_text(text: str, tag: str = "*") -> str:
        if not text:
            raise InvalidSelectorError(message="Text cannot be empty for text selector.")
        return f"{tag} >> text={text}"

    @staticmethod
    def by_label(label: str) -> str:
        if not label:
            raise InvalidSelectorError(message="Label cannot be empty.")
        return f'label:has-text("{label}")'

    @staticmethod
    def by_placeholder(placeholder: str) -> str:
        if not placeholder:
            raise InvalidSelectorError(message="Placeholder cannot be empty.")
        return f'[placeholder="{placeholder}"]'

    @staticmethod
    def by_test_id(test_id: str) -> str:
        if not test_id:
            raise InvalidSelectorError(message="Test ID cannot be empty.")
        return f'[data-testid="{test_id}"]'

    @staticmethod
    def by_role(role: str, name: str | None = None) -> str:
        if not role:
            raise InvalidSelectorError(message="Role cannot be empty.")
        if name:
            return f'role={role}[name="{name}"]'
        return f"role={role}"

    @staticmethod
    def by_aria_label(label: str) -> str:
        if not label:
            raise InvalidSelectorError(message="ARIA label cannot be empty.")
        return f'[aria-label="{label}"]'

    @staticmethod
    def by_css(selector: str) -> str:
        if not selector:
            raise InvalidSelectorError(message="CSS selector cannot be empty.")
        return selector

    @staticmethod
    def by_xpath(xpath: str) -> str:
        if not xpath:
            raise InvalidSelectorError(message="XPath cannot be empty.")
        return f"xpath={xpath}"

    @staticmethod
    def click(page: Any, selector: str, timeout_ms: float = 10000.0) -> None:
        try:
            page.click(selector, timeout=timeout_ms)
        except Exception as e:
            raise ElementNotFoundError(message=f"Failed to click element '{selector}'.") from e

    @staticmethod
    def fill(page: Any, selector: str, value: str, timeout_ms: float = 10000.0) -> None:
        try:
            page.fill(selector, value, timeout=timeout_ms)
        except Exception as e:
            raise ElementNotFoundError(message=f"Failed to fill element '{selector}' with value.") from e

    @staticmethod
    def select_option(page: Any, selector: str, value: str, timeout_ms: float = 10000.0) -> None:
        try:
            page.select_option(selector, value, timeout=timeout_ms)
        except Exception as e:
            raise ElementNotFoundError(message=f"Failed to select option '{value}' in '{selector}'.") from e

    @staticmethod
    def get_text(page: Any, selector: str, timeout_ms: float = 10000.0) -> str:
        try:
            return page.text_content(selector, timeout=timeout_ms) or ""
        except Exception as e:
            raise ElementNotFoundError(message=f"Failed to get text from element '{selector}'.") from e

    @staticmethod
    def is_visible(page: Any, selector: str) -> bool:
        try:
            return page.locator(selector).is_visible()
        except Exception:
            return False
