from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from dsutil.text import color, print_colored


@dataclass
class TableConfig:
    """Configuration for the upload history table."""

    # Colors
    title_color: str = "yellow"
    table_color: str = "blue"
    track_color: str = "blue"
    inst_color: str = "cyan"
    timestamp_color: str = "white"
    footer_color: str = "white"

    # Table dimensions
    table_width: int = 84
    filename_width: int = 48
    timestamp_width: int = 30

    # Derived row format
    row_format: str = field(init=False)

    def __post_init__(self):
        self.row_format = f" {{:<{self.filename_width}}} | {{:<{self.timestamp_width}}}"


@dataclass
class TableFormatter:
    """Print file upload table."""

    config: TableConfig = field(default_factory=TableConfig)

    def print_table(self, data: list[dict], title: str, limit: int | None = None) -> None:
        """Print a table of uploaded files."""
        self._print_title(title)
        self._print_header()
        self._print_rows(data, limit)
        self._print_footer(data, title, limit)

    def _print_title(self, title: str) -> None:
        print_colored(f"\n=== {title} ===", self.config.title_color, attrs=["bold"])

    def _print_header(self) -> None:
        line = "-" * self.config.table_width
        header_sep = "=" * self.config.table_width
        header = f"|{self.config.row_format.format('Filename', 'Uploaded')} |"

        print(color(line, self.config.table_color))
        print(
            color("|", self.config.table_color)
            + color(header[1:-2], self.config.table_color, attrs=["bold"])
            + color("|", self.config.table_color)
        )
        print(color(header_sep, self.config.table_color))

    def _print_rows(self, data: list[dict], limit: int | None) -> None:
        sorted_data = sorted(data, key=lambda x: x["uploaded"], reverse=True)
        displayed_data = sorted_data[:limit] if limit else sorted_data

        for item in displayed_data:
            self._print_row(item)

    def _print_row(self, item: dict) -> None:
        date = datetime.fromisoformat(item["uploaded"])
        formatted_date = date.strftime("%a %b %-d %Y %-I:%M:%S %p")
        formatted_row = self.config.row_format.format(item["filename"], formatted_date)

        filename_color = (
            self.config.inst_color if "No Vocals" in item["filename"] else self.config.track_color
        )
        colored_row = (
            color(formatted_row[: self.config.filename_width + 1], filename_color)
            + color(
                formatted_row[self.config.filename_width + 1 : self.config.filename_width + 3],
                self.config.table_color,
            )
            + color(formatted_row[self.config.filename_width + 3 :], self.config.timestamp_color)
        )
        print(
            color("|", self.config.table_color) + colored_row + color("|", self.config.table_color)
        )

    def _print_footer(self, data: list[dict], title: str, limit: int | None) -> None:
        if limit and len(data) > limit:
            more_items = len(data) - limit
            more_text = color("| " + " " * 81 + "|\n|", self.config.table_color)
            more_text += color(f" ... and {more_items} more", self.config.footer_color)
            more_text += color(f', see with --history "{title}"', self.config.footer_color)
            print(more_text)

        print(color("-" * self.config.table_width, self.config.table_color))
