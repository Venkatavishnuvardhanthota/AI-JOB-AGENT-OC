from __future__ import annotations

import csv
import json
import os
from typing import Any

from app.operations.config import OperationsConfig
from app.operations.exceptions import ExportError
from app.operations.interfaces import Exporter


class OperationsExporter(Exporter):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config
        os.makedirs(self._config.export_dir, exist_ok=True)

    def export_json(self, data: Any, path: str) -> str:
        full_path = self._resolve_path(path, "json")
        try:
            with open(full_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            return full_path
        except OSError as e:
            raise ExportError(f"Failed to export JSON to {full_path}: {e}") from e

    def export_csv(self, data: list[dict[str, Any]], path: str) -> str:
        if not data:
            raise ExportError("No data to export as CSV")
        full_path = self._resolve_path(path, "csv")
        try:
            with open(full_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)
            return full_path
        except OSError as e:
            raise ExportError(f"Failed to export CSV to {full_path}: {e}") from e

    def export_pdf(self, html_content: str, path: str) -> str:
        full_path = self._resolve_path(path, "pdf")
        try:
            from weasyprint import HTML

            HTML(string=html_content).write_pdf(full_path)
            return full_path
        except ImportError:
            raise ExportError("PDF export requires 'weasyprint' library") from None
        except Exception as e:
            raise ExportError(f"Failed to export PDF to {full_path}: {e}") from e

    def _resolve_path(self, path: str, extension: str) -> str:
        if not path.endswith(f".{extension}"):
            path = f"{path}.{extension}"
        if not os.path.isabs(path):
            path = os.path.join(self._config.export_dir, path)
        return path
