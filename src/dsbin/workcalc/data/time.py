from __future__ import annotations

import operator
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from polykit.formatters import Text

if TYPE_CHECKING:
    from datetime import datetime

    from dsbin.workcalc.data import WorkStats


class DayOfWeek(Enum):
    """Enum to represent the days of the week."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class TimeSpan:
    """Information about the time span of work."""

    first_item: datetime
    last_item: datetime
    span_days: int
    span_hours: int

    @classmethod
    def from_stats(cls, stats: WorkStats) -> TimeSpan | None:
        """Create TimeSpan from WorkStats."""
        if not (stats.earliest_timestamp and stats.latest_timestamp):
            return None

        time_span = stats.latest_timestamp - stats.earliest_timestamp
        span_days, remainder = divmod(time_span.total_seconds(), 86400)
        span_hours, _ = divmod(remainder, 3600)

        return cls(
            first_item=stats.earliest_timestamp,
            last_item=stats.latest_timestamp,
            span_days=int(span_days),
            span_hours=int(span_hours),
        )


@dataclass
class TimeDistribution:
    """Statistics about time distribution of work."""

    by_weekday: dict[DayOfWeek, tuple[int, float]]
    most_active_hours: list[tuple[int, int, float]]


class TimeAnalyzer:
    """Analyzes time-related patterns in work data."""

    @staticmethod
    def format_date(dt: datetime) -> str:
        """Format the date without leading zero in the day."""
        return dt.strftime("%B %-d, %Y at %-I:%M %p").replace(" 0", " ")

    @staticmethod
    def format_time_span(span: TimeSpan, item_name: str = "item") -> list[str]:
        """Format time span information for display."""
        return [
            f"First {item_name}: {TimeAnalyzer.format_date(span.first_item)}",
            f"Last {item_name}: {TimeAnalyzer.format_date(span.last_item)}",
            f"Time between first and last: {Text.plural('day', span.span_days, with_count=True)}, "
            f"{Text.plural('hour', span.span_hours, with_count=True)}",
        ]

    @staticmethod
    def calculate_time_distribution(stats: WorkStats) -> TimeDistribution:
        """Calculate time distribution statistics."""
        total_items = sum(stats.items_by_weekday.values())
        if total_items == 0:
            return TimeDistribution(by_weekday={}, most_active_hours=[])

        by_weekday = {}
        for day_value in range(7):
            day = DayOfWeek(day_value)
            items = stats.items_by_weekday[day_value]
            percentage = (items / total_items) * 100 if total_items > 0 else 0
            by_weekday[day] = (items, percentage)

        most_active_hours = []
        for hour, items in sorted(
            stats.items_by_hour.items(),
            key=operator.itemgetter(1),
            reverse=True,
        )[:3]:
            percentage = (items / total_items) * 100
            most_active_hours.append((hour, items, percentage))

        return TimeDistribution(
            by_weekday=by_weekday,
            most_active_hours=most_active_hours,
        )

    @staticmethod
    def format_distribution(dist: TimeDistribution, item_name: str = "item") -> list[str]:
        """Format time distribution statistics for display."""
        messages = []

        # Weekday distribution
        for day, (items, percentage) in dist.by_weekday.items():
            messages.append(
                f"{day.name.capitalize()}: {Text.plural(item_name, items, with_count=True)} ({percentage:.1f}%)"
            )

        # Most active hours
        messages.append("\nMost active hours:")
        for hour, items, percentage in dist.most_active_hours:
            messages.append(
                f"  {TimeAnalyzer.format_hour(hour)}: {Text.plural(item_name, items, with_count=True)} ({percentage:.1f}%)"
            )

        return messages

    @staticmethod
    def format_hour(hour: int) -> str:
        """Format hour in 12-hour format with AM/PM."""
        if hour == 0:
            return "12 AM"
        if hour < 12:
            return f"{hour} AM"
        if hour == 12:
            return "12 PM"
        return f"{hour - 12} PM"
