from __future__ import annotations

from dataclasses import dataclass, field


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
