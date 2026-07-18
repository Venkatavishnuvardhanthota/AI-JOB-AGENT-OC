"""Shared utility functions for provider framework."""

import re
from datetime import datetime, timedelta
from typing import Any


def parse_salary(text: str) -> dict[str, Any]:
    """Extract salary information from a text string.

    Handles formats like '$50,000 - $70,000 a year', '€40k-€60k', etc.
    Returns dict with min, max, currency, period keys.
    """
    if not text:
        return {"min": None, "max": None, "currency": None, "period": None}

    original = text
    text = text.strip()

    currency_map = {
        "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "CA$": "CAD",
        "A$": "AUD", "NZ$": "NZD", "CHF": "CHF", "kr": "SEK", "R$": "BRL",
        "INR": "INR", "₹": "INR", "R": "ZAR", "SGD": "SGD", "HK$": "HKD",
    }
    currency = "USD"
    for symbol, code in currency_map.items():
        if symbol in text:
            currency = code
            break

    text_clean = text.replace(",", "").replace("k", "000").replace("K", "000")
    text_clean = re.sub(r"[^0-9.\s\-–—to]", " ", text_clean)
    numbers = re.findall(r"\d+(?:\.\d+)?", text_clean)

    period = "yearly"
    lower = original.lower()
    if "hour" in lower or "hr" in lower:
        period = "hourly"
    elif "month" in lower:
        period = "monthly"
    elif "week" in lower:
        period = "weekly"
    elif "day" in lower:
        period = "daily"
    elif "year" in lower or "annual" in lower or "annum" in lower:
        period = "yearly"

    result: dict[str, Any] = {
        "min": None, "max": None,
        "currency": currency, "period": period,
    }

    if len(numbers) >= 2:
        result["min"] = _to_float(numbers[0])
        result["max"] = _to_float(numbers[1])
    elif len(numbers) == 1:
        val = _to_float(numbers[0])
        if "-" in original or "–" in original or "—" in original or "to" in original.lower():
            result["min"] = val
        else:
            result["min"] = val
            result["max"] = val * 1.2 if val > 0 else None

    return result


def _to_float(val: Any) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_relative_date(text: str) -> datetime | None:
    """Parse relative date strings like '3 days ago', 'Just posted', '30+ days ago'."""
    if not text:
        return None

    text = text.lower().strip()
    now = datetime.utcnow()

    if "just posted" in text or "moments ago" in text or "recently" in text:
        return now
    if "today" in text:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    numbers = re.findall(r"\d+", text)

    if "minute" in text or "min " in text:
        minutes = int(numbers[0]) if numbers else 0
        return now - timedelta(minutes=minutes)
    if "hour" in text or "hr " in text:
        hours = int(numbers[0]) if numbers else 0
        return now - timedelta(hours=hours)
    if "day" in text:
        days = int(numbers[0]) if numbers else 0
        return now - timedelta(days=days)
    if "week" in text:
        weeks = int(numbers[0]) if numbers else 0
        return now - timedelta(weeks=weeks)
    if "month" in text:
        months = int(numbers[0]) if numbers else 1
        return now - timedelta(days=months * 30)

    return None


def clean_text(text: str | None, max_length: int = 255) -> str | None:
    """Clean and truncate text: collapse whitespace, strip, limit length."""
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned[:max_length]


def join_url(base: str, path: str) -> str:
    """Join a base URL with a path, handling slashes correctly."""
    base = base.rstrip("/")
    path = path.lstrip("/")
    return f"{base}/{path}"


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    return pattern.findall(text)


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    pattern = re.compile(r"https?://[^\s]+")
    return pattern.findall(text)
