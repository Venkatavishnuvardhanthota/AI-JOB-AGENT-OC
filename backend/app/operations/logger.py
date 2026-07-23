from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from app.operations.config import OperationsConfig
from app.operations.exceptions import LoggingError
from app.operations.interfaces import StructuredLogger


class OperationsStructuredLogger(StructuredLogger):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config
        self._logger = structlog.get_logger(__name__).bind(service="operations")

    def _log(
        self,
        level: str,
        message: str,
        **kwargs: Any,
    ) -> None:
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "module": kwargs.pop("module", None),
                "component": kwargs.pop("component", None),
                "correlation_id": kwargs.pop("correlation_id", None),
                "orchestration_id": kwargs.pop("orchestration_id", None),
                "application_id": kwargs.pop("application_id", None),
                "provider": kwargs.pop("provider", None),
                "stage": kwargs.pop("stage", None),
                "duration": kwargs.pop("duration", None),
                "message": message,
                "exception": kwargs.pop("exception", None),
                "metadata": kwargs,
            }
            entry = {k: v for k, v in entry.items() if v is not None}
            log_method = getattr(self._logger, level.lower(), self._logger.info)
            log_method(message, **entry)
        except Exception as e:
            raise LoggingError(f"Failed to emit log entry: {e}") from e

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("debug", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("error", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log("critical", message, **kwargs)
