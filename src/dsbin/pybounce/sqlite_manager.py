# ruff: noqa: D102

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from polykit.cli import walking_man
from polykit.core import async_retry_on_exception, polykit_setup
from polykit.log import Logician

if TYPE_CHECKING:
    from dsbin.pybounce.client_protocol import TelegramClientProtocol

polykit_setup()

logger = Logician.get_logger(level="info")


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
        with walking_man(color="cyan"):
            await self.client.start()

    @async_retry_on_exception(
        sqlite3.OperationalError, tries=RETRY_TRIES, delay=RETRY_DELAY, logger=logger
    )
    async def disconnect_client(self) -> None:
        """Disconnects the client safely, retrying if a sqlite3.OperationalError occurs."""
        await self.client.disconnect()
