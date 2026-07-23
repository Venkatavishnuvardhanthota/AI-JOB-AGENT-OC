from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BrowserConfig:
    cache_ttl_seconds: int = 300
    default_timeout_ms: float = 30000.0
    navigation_timeout_ms: float = 60000.0
    wait_timeout_ms: float = 10000.0
    headless: bool = True
    slow_mo: int = 0
    viewport_width: int = 1920
    viewport_height: int = 1080
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    downloads_path: str = "downloads"
    screenshot_path: str = "screenshots"
    max_screenshot_files: int = 100
    max_upload_size_mb: int = 10
    allowed_upload_extensions: tuple[str, ...] = (".pdf", ".doc", ".docx", ".txt", ".rtf")
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    max_contexts_per_browser: int = 5
    max_pages_per_context: int = 10
    cleanup_on_close: bool = True
