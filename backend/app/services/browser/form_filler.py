import logging
import time

from app.services.browser.base import BaseBrowserClient
from app.services.browser.types import (
    FormFieldType,
    SiteConfig,
    StepResult,
)

logger = logging.getLogger(__name__)


class FormFiller:
    def __init__(self, browser: BaseBrowserClient) -> None:
        self._browser = browser

    async def fill_form(
        self,
        fields: list[dict],
        site_config: SiteConfig | None = None,
    ) -> list[StepResult]:
        results: list[StepResult] = []
        for field in fields:
            selector = field.get("selector", "")
            value = field.get("value", "")
            field_type = field.get("field_type", "text")
            if not selector:
                continue
            step_name = f"fill_{field_type}_{selector.replace(' ', '_')}"
            start = time.monotonic()
            success = await self._fill_single_field(selector, value, field_type)
            elapsed = int((time.monotonic() - start) * 1000)
            if success:
                logger.info("Filled %s at %s", field_type, selector)
            else:
                logger.warning("Failed to fill %s at %s", field_type, selector)
            results.append(StepResult(
                step_name=step_name[:100],
                success=success,
                duration_ms=elapsed,
                error=None if success else f"Failed to fill {field_type} at {selector}",
            ))
        return results

    async def upload_resume(self, selector: str, file_path: str) -> StepResult:
        return await self._upload_file("resume", selector, file_path)

    async def upload_cover_letter(self, selector: str, file_path: str) -> StepResult:
        return await self._upload_file("cover_letter", selector, file_path)

    async def upload_certificate(self, selector: str, file_path: str) -> StepResult:
        return await self._upload_file("certificate", selector, file_path)

    async def click_submit(self, selector: str) -> StepResult:
        start = time.monotonic()
        success = await self._browser.click_submit(selector) if selector else False
        elapsed = int((time.monotonic() - start) * 1000)
        return StepResult(
            step_name="submit_form",
            success=success,
            duration_ms=elapsed,
            error=None if success else f"Failed to submit at {selector}",
        )

    async def _fill_single_field(self, selector: str, value: str, field_type: str) -> bool:
        try:
            if field_type == FormFieldType.TEXT:
                return await self._browser.fill_text(selector, value)
            elif field_type == FormFieldType.TEXTAREA:
                return await self._browser.fill_textarea(selector, value)
            elif field_type == FormFieldType.CHECKBOX:
                checked = value.lower() in ("true", "yes", "1")
                return await self._browser.click_checkbox(selector, checked)
            elif field_type == FormFieldType.DROPDOWN:
                return await self._browser.select_dropdown(selector, value)
            elif field_type == FormFieldType.RADIO:
                return await self._browser.click_radio(selector)
            elif field_type == FormFieldType.FILE:
                return await self._browser.upload_file(selector, value)
            else:
                logger.warning("Unknown field type: %s", field_type)
                return False
        except Exception as e:
            logger.error("Error filling field %s: %s", selector, e)
            return False

    async def _upload_file(self, file_type: str, selector: str, file_path: str) -> StepResult:
        start = time.monotonic()
        success = False
        if selector and file_path:
            success = await self._browser.upload_file(selector, file_path)
        elapsed = int((time.monotonic() - start) * 1000)
        return StepResult(
            step_name=f"upload_{file_type}",
            success=success,
            duration_ms=elapsed,
            error=None if success else f"Failed to upload {file_type}",
        )
