from __future__ import annotations

import logging
import os
import sys

import structlog

from app.core.config import settings


def _add_request_id(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    use_json = os.environ.get("LOG_FORMAT", "").lower() == "json"

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        _add_request_id,
        structlog.stdlib.ExtraAdder(),
    ]

    if use_json:
        processors = shared_processors + [
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.DEBUG)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )


logger: structlog.stdlib.BoundLogger = structlog.get_logger()
