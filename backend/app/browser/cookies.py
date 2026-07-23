from __future__ import annotations

from typing import Any

from app.browser.exceptions import CookieError
from app.browser.schemas import Cookie


class CookieManager:
    @staticmethod
    def get_cookies(page: Any) -> list[Cookie]:
        try:
            raw = page.context.cookies()
            return [
                Cookie(
                    name=c["name"],
                    value=c["value"],
                    domain=c.get("domain"),
                    path=c.get("path"),
                    expires=c.get("expires"),
                    http_only=c.get("httpOnly", False),
                    secure=c.get("secure", False),
                    same_site=c.get("sameSite"),
                )
                for c in raw
            ]
        except Exception as e:
            raise CookieError(message=f"Failed to get cookies: {e!s}") from e

    @staticmethod
    def set_cookies(page: Any, cookies: list[Cookie]) -> None:
        try:
            page.context.add_cookies(
                [
                    {
                        "name": c.name,
                        "value": c.value,
                        "domain": c.domain,
                        "path": c.path,
                        "expires": c.expires,
                        "httpOnly": c.http_only,
                        "secure": c.secure,
                        "sameSite": c.same_site,
                    }
                    for c in cookies
                ]
            )
        except Exception as e:
            raise CookieError(message=f"Failed to set cookies: {e!s}") from e

    @staticmethod
    def clear_cookies(page: Any) -> None:
        try:
            page.context.clear_cookies()
        except Exception as e:
            raise CookieError(message=f"Failed to clear cookies: {e!s}") from e

    @staticmethod
    def get_cookie(page: Any, name: str) -> Cookie | None:
        cookies = CookieManager.get_cookies(page)
        for c in cookies:
            if c.name == name:
                return c
        return None
