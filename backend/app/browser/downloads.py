from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

from app.browser.schemas import DownloadInfo


class DownloadManager:
    def __init__(self, downloads_path: str = "downloads") -> None:
        self._downloads_path = downloads_path
        self._downloads: dict[str, DownloadInfo] = {}
        os.makedirs(self._downloads_path, exist_ok=True)

    def capture_download(self, page: Any, timeout_ms: float = 60000.0) -> DownloadInfo:
        download_id = str(uuid.uuid4())
        info = DownloadInfo(id=download_id, downloaded_at=datetime.utcnow())
        try:
            with page.expect_download(timeout=timeout_ms) as download_info:
                download = download_info.value
            suggested = download.suggested_filename
            file_path = os.path.join(self._downloads_path, f"{download_id}_{suggested}" if suggested else download_id)
            download.save_as(file_path)
            info.suggested_filename = suggested
            info.file_path = file_path
            info.file_size_bytes = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
            info.success = True
        except Exception as e:
            info.success = False
            info.error = str(e)
        self._downloads[download_id] = info
        return info

    def capture_download_by_click(
        self,
        page: Any,
        selector: str,
        timeout_ms: float = 60000.0,
    ) -> DownloadInfo:
        download_id = str(uuid.uuid4())
        info = DownloadInfo(id=download_id, downloaded_at=datetime.utcnow())
        try:
            with page.expect_download(timeout=timeout_ms) as download_info:
                page.click(selector, timeout=timeout_ms)
                download = download_info.value
            suggested = download.suggested_filename
            file_path = os.path.join(self._downloads_path, f"{download_id}_{suggested}" if suggested else download_id)
            download.save_as(file_path)
            info.suggested_filename = suggested
            info.file_path = file_path
            info.file_size_bytes = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
            info.success = True
        except Exception as e:
            info.success = False
            info.error = str(e)
        self._downloads[download_id] = info
        return info

    def get_download(self, download_id: str) -> DownloadInfo | None:
        return self._downloads.get(download_id)

    def list_downloads(self) -> list[DownloadInfo]:
        return list(self._downloads.values())

    def clear(self) -> None:
        self._downloads.clear()

    def verify_download(self, file_path: str) -> bool:
        return os.path.isfile(file_path) and os.path.getsize(file_path) > 0
