"""Shared pydantic field validators for career profile schemas."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import ValidationError


def normalize_url(value: str | None) -> str | None:
    """Strip whitespace and require a valid http(s) scheme."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    parsed = urlparse(value)
    if not parsed.netloc or not parsed.scheme:
        raise ValueError("URL must be a valid absolute URL")
    return value


def validate_url(value: str | None) -> str | None:
    return normalize_url(value)


def title_case(value: str | None) -> str | None:
    """Strip whitespace from string fields."""
    if value is None:
        return None
    value = value.strip()
    return value or None
