# ruff: noqa: D102

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any, Protocol

from dsbase import LocalLogger, configure_traceback
from dsbase.animation import walking_animation
from dsbase.tools import async_retry_on_exception

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from telethon.tl.types import Channel, Chat, DocumentAttributeAudio

configure_traceback()
logger = LocalLogger().get_logger(level="info")


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


class SQLiteManager:
    """Manages the SQLite database for the Telegram client."""

    # Retry configuration
    RETRY_TRIES = 5
    RETRY_DELAY = 5

    def __init__(self, client: TelegramClientProtocol) -> None:
        self.client = client

    @async_retry_on_exception(
        sqlite3.OperationalError, tries=RETRY_TRIES, delay=RETRY_DELAY, logger=logger
    )
    async def start_client(self) -> None:
        """Start the client safely, retrying if a sqlite3.OperationalError occurs."""
        with walking_animation():
            await self.client.start()

    @async_retry_on_exception(
        sqlite3.OperationalError, tries=RETRY_TRIES, delay=RETRY_DELAY, logger=logger
    )
    async def disconnect_client(self) -> None:
        """Disconnects the client safely, retrying if a sqlite3.OperationalError occurs."""
        await self.client.disconnect()
