from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from .db_manager import DatabaseManager
from .table_formatter import TableFormatter

from dsutil import LocalLogger

if TYPE_CHECKING:
    from .wp_config import Config

tz = ZoneInfo("America/New_York")


class UploadTracker:
    """Track, log, and print file uploads."""

    def __init__(self, config: Config):
        self.config = config
        self.db = DatabaseManager(config)
        self.logger = LocalLogger.setup_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            message_only=self.config.log_message_only,
        )

        # Track the current set of uploads before recording them to the upload log
        self.current_upload_set = defaultdict(dict)

    def log_upload_set(self) -> None:
        """Log the current set of uploads and clear the set."""
        if not self.current_upload_set:
            return

        # Get current time and format it for MySQL
        uploaded = datetime.now(tz=tz).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")

        self.db.record_upload_set_to_db(uploaded, self.current_upload_set)
        self.current_upload_set.clear()

    def pretty_print_history(self, track_name: str | None = None) -> None:
        """Print the upload history in a neatly organized way with color."""
        history = self.db.get_upload_history(track_name)
        table_formatter = TableFormatter(apply_limit=track_name is None)
        num_uploads = table_formatter.config.uploads_per_song

        self.logger.info(
            "Listing %s uploads for %s (latest first).",
            f"latest {num_uploads}" if not track_name else "all",
            f'"{track_name}"' if track_name else "all tracks",
        )

        for entry in history:
            table_formatter.print_table(entry["uploads"], entry["track_name"])
