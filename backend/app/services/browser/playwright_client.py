import logging
import time
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class PlaywrightBrowserClient:
    """Manages a Playwright browser instance for form automation."""

    def __init__(self, screenshot_dir: str | None = None) -> None:
        self._browser = None
        self._context = None
        self._page = None
        self._playwright = None
        self._screenshot_dir = Path(screenshot_dir or f"{settings.UPLOAD_DIR}/screenshots")
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._launched = False

    async def start(self) -> None:
        if self._launched:
            return
        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            self._page = await self._context.new_page()
            self._launched = True
            logger.info("Browser launched successfully")
        except ImportError:
            logger.error(
                "Playwright is not installed. "
                "Run: pip install playwright && playwright install chromium"
            )
            raise
        except Exception as e:
            logger.error("Failed to launch browser: %s", str(e))
            await self.close()
            raise

    async def close(self) -> None:
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.warning("Error closing browser: %s", str(e))
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
            self._launched = False

    async def navigate(self, url: str) -> None:
        if not self._page:
            raise RuntimeError("Browser not started")
        logger.info("Navigating to %s", url)
        await self._page.goto(url, wait_until="networkidle", timeout=30000)

    async def fill_text(self, selector: str, value: str) -> bool:
        return await self._fill_field(selector, value, "text")

    async def fill_textarea(self, selector: str, value: str) -> bool:
        return await self._fill_field(selector, value, "textarea")

    async def click_checkbox(self, selector: str, checked: bool) -> bool:
        if not self._page:
            return False
        try:
            is_checked = await self._page.is_checked(selector)
            if is_checked != checked:
                await self._page.click(selector)
            return True
        except Exception as e:
            logger.warning("Failed to toggle checkbox %s: %s", selector, e)
            return False

    async def select_dropdown(self, selector: str, value: str) -> bool:
        if not self._page:
            return False
        try:
            await self._page.select_option(selector, value)
            return True
        except Exception as e:
            logger.warning("Failed to select dropdown %s: %s", selector, e)
            return False

    async def click_radio(self, selector: str) -> bool:
        if not self._page:
            return False
        try:
            await self._page.click(selector)
            return True
        except Exception as e:
            logger.warning("Failed to click radio %s: %s", selector, e)
            return False

    async def upload_file(self, selector: str, file_path: str) -> bool:
        if not self._page:
            return False
        try:
            file_input = self._page.locator(selector)
            await file_input.set_input_files(file_path)
            logger.info("Uploaded file %s to %s", file_path, selector)
            return True
        except Exception as e:
            logger.warning("Failed to upload file %s: %s", selector, e)
            return False

    async def click_submit(self, selector: str) -> bool:
        if not self._page:
            return False
        try:
            await self._page.click(selector)
            await self._page.wait_for_load_state("networkidle", timeout=15000)
            return True
        except Exception as e:
            logger.warning("Failed to click submit %s: %s", selector, e)
            return False

    async def wait_for_selector(self, selector: str, timeout_ms: int = 10000) -> bool:
        if not self._page:
            return False
        try:
            await self._page.wait_for_selector(selector, timeout=timeout_ms)
            return True
        except Exception:
            return False

    async def is_element_present(self, selector: str) -> bool:
        if not self._page:
            return False
        try:
            return await self._page.locator(selector).count() > 0
        except Exception:
            return False

    async def take_screenshot(self, name: str) -> str | None:
        if not self._page:
            return None
        try:
            timestamp = int(time.time())
            filename = f"{name}_{timestamp}.png"
            filepath = str(self._screenshot_dir / filename)
            await self._page.screenshot(path=filepath, full_page=True)
            logger.info("Screenshot saved: %s", filepath)
            return filepath
        except Exception as e:
            logger.warning("Failed to take screenshot %s: %s", name, e)
            return None

    async def get_page_title(self) -> str:
        if not self._page:
            return ""
        try:
            return await self._page.title()
        except Exception:
            return ""

    async def get_current_url(self) -> str:
        if not self._page:
            return ""
        try:
            return self._page.url
        except Exception:
            return ""

    async def _fill_field(self, selector: str, value: str, field_type: str) -> bool:
        if not self._page:
            return False
        try:
            element = self._page.locator(selector)
            if field_type == "textarea":
                await element.fill(value)
            else:
                await element.fill(value)
            return True
        except Exception as e:
            logger.warning("Failed to fill %s %s: %s", field_type, selector, e)
            return False
