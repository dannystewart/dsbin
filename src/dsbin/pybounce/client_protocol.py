# ruff: noqa: D102

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from polykit.core import polykit_setup
from polykit.log import Logician

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from telethon.tl.types import Channel, Chat, DocumentAttributeAudio

polykit_setup()

logger = Logician.get_logger(level="info")


class TelegramClientProtocol(Protocol):
    """Protocol for the Telegram client."""

    async def start(
        self,
        phone: Callable[[], str] | str | None = None,
        password: Callable[[], str] | str | None = None,
        *,
        bot_token: str | None = None,
        force_sms: bool = False,
        code_callback: Callable[[], str | int] | None = None,
        first_name: str = "New User",
        last_name: str = "",
        max_attempts: int = 3,
    ) -> Any: ...

    async def disconnect(self) -> None: ...

    async def get_entity(self, entity: str) -> Channel | Chat: ...

    async def send_file(
        self,
        entity: Channel | Chat,
        file: str | bytes | Path,
        caption: str | None = None,
        attributes: list[DocumentAttributeAudio] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Any: ...
