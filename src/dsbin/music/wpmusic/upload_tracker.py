from __future__ import annotations

import operator
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from .db_manager import DatabaseManager

from dsutil import LocalLogger

if TYPE_CHECKING:
    from .wp_config import Config

tz = ZoneInfo("America/New_York")

console = Console()


@dataclass
class TableConfig:
    """Configuration for the upload history table."""

    # Uploads per song when displaying all songs
    uploads_per_song: int = 3

    # Date format
    date_format: str = "%a %m.%d.%Y %I:%M %p"

    # Colors
    header_color: str = "yellow"
    track_color: str = "cyan"
    indicator_color: str = "green"
    timestamp_color: str = "white"
    footer_color: str = "cyan"

    # Column widths
    file_col_width: int = 36
    inst_col_width: int = 7
    time_col_width: int = 23

    # Instrumental indicator
    inst_indicator: str = "✓"
    space_before_indicator: int = 2
    indicator_length: int = field(init=False)

    def __post_init__(self):
        self.indicator_length = len(self.inst_indicator)
        self.inst_indicator = " " * self.space_before_indicator + self.inst_indicator


class UploadTracker:
    """Track, log, and print file uploads."""

    def __init__(self, config: Config):
        self.config = config
        self.table_config = TableConfig()
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
        """Print the upload history in a beautifully formatted display."""
        history = self.db.get_upload_history(track_name)
        uploads_per_song = TableConfig().uploads_per_song
        num_uploads = uploads_per_song if not track_name else None

        # Create header with fixed width
        header_text = Text()
        header_text.append("Upload History", style="bold blue")
        if track_name:
            header_text.append(" for ", style="dim")
            header_text.append(f'"{track_name}"', style="bold yellow")
        else:
            header_text.append(
                f" (showing latest {num_uploads} uploads per track)", style="dim italic"
            )

        # Process and display each track's history
        for entry in history:
            table = Table(border_style="dim", padding=(0, 1), box=box.HORIZONTALS)

            table.add_column(
                f"[yellow]{entry['track_name']}[/yellow]", style="cyan", width=36, no_wrap=True
            )
            table.add_column("[yellow]Inst[/yellow]", justify="center", style="green", width=4)
            table.add_column("[yellow]Uploaded[/yellow]", style="white", width=24)

            # Process uploads to pair instrumentals with their main tracks
            processed_uploads = self._prepare_rows_for_display(entry["uploads"])
            display_uploads = processed_uploads[:num_uploads] if num_uploads else processed_uploads

            for upload, has_inst in display_uploads:
                filename = Text(upload["filename"], overflow="ellipsis")
                date = datetime.fromisoformat(upload["uploaded"])
                formatted_date = date.strftime("%a %m.%d.%Y %I:%M %p")

                # Show ✓ for tracks that have instrumentals
                has_inst = "[bold]✓[/bold]" if has_inst else ""
                table.add_row(filename, has_inst, formatted_date)

            console.print(table)

            if num_uploads and len(processed_uploads) > num_uploads:
                more_count = len(processed_uploads) - num_uploads
                console.print(
                    Text(
                        f" ...and {more_count} more. Use --history \"{entry['track_name']}\" to see all.",
                        style="dim italic",
                    ),
                    width=80,
                )

    def _prepare_rows_for_display(self, data: list[dict]) -> list[tuple[dict, bool]]:
        """Process rows to combine main tracks with their instrumentals and skip duplicates."""
        # First pass: Handle instrumental pairing
        paired_rows = []
        prev_item = None

        sorted_data = sorted(data, key=operator.itemgetter("uploaded"), reverse=True)

        for item in sorted_data:
            has_matching_inst = False

            # For non-instrumental tracks, check if the previous item was its instrumental
            if not item["instrumental"] and prev_item is not None:
                current_version = self._get_version(item["filename"])
                prev_version = self._get_version(prev_item["filename"])

                if prev_item["instrumental"] and current_version == prev_version:
                    has_matching_inst = True
                    paired_rows.pop()  # Remove the instrumental entry

            paired_rows.append((item, has_matching_inst))
            prev_item = item

        # Second pass: Remove duplicates
        final_rows = []
        prev_filename = None

        for item, has_inst in paired_rows:
            if item["filename"] != prev_filename:
                final_rows.append((item, has_inst))
                prev_filename = item["filename"]

        return final_rows

    @staticmethod
    def _get_version(filename: str) -> str:
        """Remove suffix and extract version number from filename."""
        base = filename.rsplit(".", 1)[0].replace(" No Vocals", "")
        return base.split()[-1]
