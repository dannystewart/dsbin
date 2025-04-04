from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from polykit.parsers import Text

if TYPE_CHECKING:
    from datetime import date, datetime


@dataclass
class FormattedTime:
    """Helper class for formatting time values."""

    days: int
    hours: int
    minutes: int
    total_hours: int

    @classmethod
    def from_minutes(cls, minutes: float) -> FormattedTime:
        """Create FormattedTime from total minutes."""
        total_hours = round(minutes / 60)
        days, remainder = divmod(round(minutes), 24 * 60)
        hours, minutes = divmod(remainder, 60)
        return cls(days, hours, minutes, total_hours)

    def __str__(self) -> str:
        """Format the time as a string."""
        days_str = f"{Text.plural('day', self.days, with_count=True)}, " if self.days else ""
        return (
            f"{days_str}{Text.plural('hour', self.hours, with_count=True)}, "
            f"{Text.plural('minute', self.minutes, with_count=True)} "
            f"({self.total_hours} hours)"
        )


@dataclass
class WorkStats:
    """Statistics about work patterns across any data source."""

    source_type: str
    total_items: int = 0
    total_time: int = 0
    earliest_timestamp: datetime | None = None
    latest_timestamp: datetime | None = None
    session_count: int = 0
    items_by_day: defaultdict[date, int] = field(default_factory=lambda: defaultdict(int))
    items_by_hour: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    items_by_weekday: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    time_by_day: defaultdict[date, int | float] = field(default_factory=lambda: defaultdict(int))
    longest_session: tuple[datetime | None, int] = field(default_factory=lambda: (None, 0))
    longest_streak: tuple[date | None, int] = field(default_factory=lambda: (None, 0))
    source_metadata: dict[str, Any] = field(default_factory=dict)

    def update_timestamp_stats(self, timestamp: datetime) -> None:
        """Update statistics based on a new timestamp."""
        if self.earliest_timestamp is None or timestamp < self.earliest_timestamp:
            self.earliest_timestamp = timestamp
        if self.latest_timestamp is None or timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

        self.items_by_day[timestamp.date()] += 1
        self.items_by_hour[timestamp.hour] += 1
        self.items_by_weekday[timestamp.weekday()] += 1


# in minutes
