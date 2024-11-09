from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from dsutil.text import color, print_colored


@dataclass
class TableConfig:
    """Configuration for the upload history table."""

    # Uploads per song when displaying all songs
    uploads_per_song: int = 4

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


@dataclass
class TableFormatter:
    """Print file upload table."""

    config: TableConfig = field(default_factory=TableConfig)
    apply_limit: bool = False
    limit: int | None = field(init=False)

    def __post_init__(self):
        self.limit = self.config.uploads_per_song if self.apply_limit else None

    def print_table(self, data: list[dict], title: str) -> None:
        """Print a table of uploaded files."""
        self.print_header(title)
        self.print_rows(data)
        self.print_footer(data, title)

    def print_header(self, title: str) -> None:
        """Print the header for the upload history table."""
        print_colored(
            (
                f"\n{title:<{self.config.file_col_width}} "
                f"{"Inst":<{self.config.inst_col_width}}"
                f"{"Uploaded":<{self.config.time_col_width}}"
            ),
            self.config.header_color,
            attrs=["bold", "underline"],
        )

    def print_rows(self, data: list[dict]) -> None:
        """Print the rows of the upload history table."""
        rows = self._prepare_rows_for_display(data)
        for item, has_inst in rows:
            indicator = (
                color(self.config.inst_indicator, self.config.indicator_color, attrs=["bold"])
                if has_inst
                else ""
            )
            indicator_spacing = " " * (
                self.config.inst_col_width - (len(self.config.inst_indicator) if has_inst else 0)
            )
            date = datetime.fromisoformat(item["uploaded"])
            formatted_date = date.strftime(self.config.date_format)

            print(
                color(
                    f"{item['filename']:<{self.config.file_col_width}} ",
                    self.config.track_color,
                )
                + indicator
                + indicator_spacing
                + color(formatted_date, self.config.timestamp_color)
            )

    def print_footer(self, data: list[dict], title: str) -> None:
        """Print the table footer, with a message about more items if applicable."""
        if self.limit:  # Process first to get grouped count rather than total
            processed_rows = self._prepare_rows_for_display(data, apply_limit=False)
            rows = len(processed_rows)

            if rows > self.limit:
                more_items = rows - self.limit
                more_text = color(f"...and {more_items} more", self.config.track_color)
                more_text += color(", use ", self.config.footer_color)
                more_text += color(f'--history "{title}"', self.config.footer_color, attrs=["bold"])
                more_text += color(" to show all", self.config.footer_color)
                print(more_text)

    def _prepare_rows_for_display(
        self, data: list[dict], apply_limit: bool = True
    ) -> list[tuple[dict, bool]]:
        """Process rows to combine main tracks with their instrumentals."""
        rows = []
        prev_item = None

        sorted_data = sorted(data, key=lambda x: x["uploaded"], reverse=True)

        for item in sorted_data:
            has_matching_inst = False

            # For non-instrumental tracks, check if the previous item was its instrumental
            if not item["instrumental"] and prev_item is not None:
                current_version = self._get_version(item["filename"])
                prev_version = self._get_version(prev_item["filename"])

                if prev_item["instrumental"] and current_version == prev_version:
                    has_matching_inst = True
                    rows.pop()  # Don't add the previous instrumental to processed_rows

            rows.append((item, has_matching_inst))
            prev_item = item

        return rows[: self.limit] if apply_limit and self.limit else rows

    def _get_version(self, filename: str) -> str:
        """Remove suffix and extract version number from filename."""
        base = filename.rsplit(".", 1)[0].replace(" No Vocals", "")
        return base.split()[-1]
