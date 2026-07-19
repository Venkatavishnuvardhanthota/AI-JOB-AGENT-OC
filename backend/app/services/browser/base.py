import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseBrowserClient(ABC):
    @abstractmethod
    async def start(self) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def navigate(self, url: str) -> None:
        ...

    @abstractmethod
    async def fill_text(self, selector: str, value: str) -> bool:
        ...

    @abstractmethod
    async def fill_textarea(self, selector: str, value: str) -> bool:
        ...

    @abstractmethod
    async def click_checkbox(self, selector: str, checked: bool) -> bool:
        ...

    @abstractmethod
    async def select_dropdown(self, selector: str, value: str) -> bool:
        ...

    @abstractmethod
    async def click_radio(self, selector: str) -> bool:
        ...

    @abstractmethod
    async def upload_file(self, selector: str, file_path: str) -> bool:
        ...

    @abstractmethod
    async def click_submit(self, selector: str) -> bool:
        ...

    @abstractmethod
    async def wait_for_selector(self, selector: str, timeout_ms: int = 10000) -> bool:
        ...

    @abstractmethod
    async def is_element_present(self, selector: str) -> bool:
        ...

    @abstractmethod
    async def take_screenshot(self, name: str) -> str | None:
        ...

    @abstractmethod
    async def get_page_title(self) -> str:
        ...

    @abstractmethod
    async def get_current_url(self) -> str:
        ...
