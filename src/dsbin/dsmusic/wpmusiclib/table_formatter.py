from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from dsutil.text import color, print_colored


@dataclass
class TableConfig:
    """Configuration for the upload history table."""

    # Uploads per song when displaying all songs
    uploads_per_song: int = 5

    # Colors
    title_color: str = "yellow"
    table_color: str = "blue"
    track_color: str = "green"
    inst_color: str = "cyan"
    timestamp_color: str = "white"
    footer_color: str = "cyan"

    # Table dimensions
    table_width: int = 84
    filename_width: int = 50
    timestamp_width: int = 30
    padding_length: int = 8

    indicator: str = "+ inst"
    indicator_length: int = field(init=False)
    space_before_indicator: int = 2

    row_format: str = field(init=False)

    def __post_init__(self):
        self.indicator_length = len(self.indicator)
        self.row_format = f" {{:<{self.filename_width}}} | {{:<{self.timestamp_width}}}"


@dataclass
class TableFormatter:
    """Print file upload table."""

    config: TableConfig = field(default_factory=TableConfig)
    use_limit: bool = False
    limit: int | None = field(init=False)

    def __post_init__(self):
        self.limit = self.config.uploads_per_song if self.use_limit else None

    def print_table(self, data: list[dict], title: str) -> None:
        """Print a table of uploaded files."""
        self.print_title(title)
        self.format_header()
        self.print_rows(data)
        self.print_footer(data, title)

    def print_title(self, title: str) -> None:
        """Print the title row containing the song name."""
        print_colored(f"\n=== {title} ===", self.config.title_color, attrs=["bold"])

    def format_header(self) -> None:
        """Print the table header with 'Filename' and 'Uploaded' column names."""
        line = "-" * self.config.table_width
        header_sep = "=" * self.config.table_width
        padding_length = self.config.padding_length

        filename_padding = self.config.filename_width - padding_length - 2
        uploaded_padding = self.config.timestamp_width - padding_length - 1

        header = f"| Filename{' ' * filename_padding} | Uploaded{' ' * uploaded_padding} | "

        self._print_header(line, header, header_sep)

    def _print_header(self, line: str, header: str, header_sep: str) -> None:
        print(color(line, self.config.table_color))
        print(
            color("|", self.config.table_color)
            + color(header[1:-2], self.config.table_color, attrs=["bold"])
            + color("|", self.config.table_color)
        )
        print(color(header_sep, self.config.table_color))

    def print_rows(self, data: list[dict]) -> None:
        """Print all rows of the table containing each uploaded file entry."""
        sorted_data = sorted(data, key=lambda x: x["uploaded"], reverse=True)

        # Process all rows first
        processed_rows = []
        prev_item = None

        for item in sorted_data:
            has_matching_inst = False

            # For non-instrumental tracks, check if previous item was its instrumental
            if not item["instrumental"] and prev_item is not None:
                current_version = self._get_version(item["filename"])
                prev_version = self._get_version(prev_item["filename"])

                if prev_item["instrumental"] and current_version == prev_version:
                    has_matching_inst = True
                    processed_rows.pop()  # Don't add the previous instrumental to processed_rows

            processed_rows.append((item, has_matching_inst))
            prev_item = item

        # Apply limit after processing
        displayed_rows = processed_rows[: self.limit] if self.limit else processed_rows

        # Print processed rows
        for item, has_inst in displayed_rows:
            self.print_row(item, has_inst)

    def print_row(self, item: dict, has_inst: bool = False) -> None:
        """Print a row of the table containing a single uploaded file entry."""
        date = datetime.fromisoformat(item["uploaded"])
        formatted_date = date.strftime("%a %b %-d %Y %-I:%M:%S %p")
        padding = " " * self.config.padding_length
        timestamp_start = self.config.filename_width + 2
        end_padding = self.config.padding_length + 2

        # Format the base filename, add consistent padding for alignment, and colorize
        filename = item["filename"]
        formatted_row = self.config.row_format.format(filename + padding, formatted_date)
        base_colored = self._colorize_row_segments(formatted_row)

        # If we need to add the indicator, replace the padding with the colored indicator
        if has_inst:
            row = self._format_row_with_instrumental(base_colored, timestamp_start, end_padding)
        else:  # For non-indicator rows, trim the padding to match the alignment
            row = self._format_row_without_instrumental(base_colored, timestamp_start, end_padding)

        print(color("|", self.config.table_color) + row + color("|", self.config.table_color))

    def _colorize_row_segments(self, row: str) -> str:
        """Add the appropriate colors to each segment of the table row for a file."""
        width = self.config.filename_width
        return (
            color(row[: width + 1], self.config.track_color)
            + color(row[width + 1 : width + 3], self.config.table_color)
            + color(row[width + 3 :], self.config.timestamp_color)
        )

    def _format_row_with_instrumental(self, row: str, timestamp_start: int, padding: int) -> str:
        """Format a row for a file that has a corresponding instrumental uploaded."""
        return (
            row[: timestamp_start - padding]
            + " " * self.config.space_before_indicator
            + color("+ inst", self.config.inst_color)
            + row[timestamp_start:]
        )

    def _format_row_without_instrumental(self, row: str, timestamp_start: int, padding: int) -> str:
        """Format a row for a file that does not have a corresponding instrumental uploaded."""
        return (
            row[: timestamp_start - padding]
            + " " * (self.config.space_before_indicator + self.config.indicator_length)
            + row[timestamp_start:]
        )

    def print_footer(self, data: list[dict], title: str) -> None:
        """Print the table footer, with a message about more items if applicable."""
        if self.limit and len(data) > self.limit:
            more_items = len(data) - self.limit
            more_text = color("| " + " " * 81 + "|\n|", self.config.table_color)
            more_text += color(f" ... and {more_items} more", self.config.footer_color)
            more_text += color(f', see with --history "{title}"', self.config.footer_color)
            print(more_text)

        print(color("-" * self.config.table_width, self.config.table_color))

    def _get_version(self, filename: str) -> str:
        """Remove suffix and extract version number from filename."""
        base = filename.rsplit(".", 1)[0].replace(" No Vocals", "")
        return base.split()[-1]
