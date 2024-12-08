from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from .summary import WorkStats


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
    """Information about the time span of commits."""

    first_commit: datetime
    last_commit: datetime
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
            first_commit=stats.earliest_timestamp,
            last_commit=stats.latest_timestamp,
            span_days=int(span_days),
            span_hours=int(span_hours),
        )


@dataclass
class TimeDistribution:
    """Statistics about time distribution of commits."""

    by_weekday: dict[DayOfWeek, tuple[int, float]]
    most_active_hours: list[tuple[int, int, float]]


def format_date(dt: datetime) -> str:
    """Format the date without leading zero in the day."""
    return dt.strftime("%B %-d, %Y at %-I:%M %p").replace(" 0", " ")


def format_time_span(span: TimeSpan) -> list[str]:
    """Format time span information for display."""
    return [
        f"First commit: {format_date(span.first_commit)}",
        f"Last commit: {format_date(span.last_commit)}",
        f"Time between first and last: {span.span_days} days, {span.span_hours} hours",
    ]


def calculate_time_distribution(stats: WorkStats) -> TimeDistribution:
    """Calculate time distribution statistics."""
    total_commits = sum(stats.commits_by_weekday.values())

    by_weekday = {}
    for day in DayOfWeek:
        commits = stats.commits_by_weekday[day.value]
        percentage = (commits / total_commits) * 100
        by_weekday[day] = (commits, percentage)

    most_active_hours = []
    for hour, commits in sorted(
        stats.commits_by_hour.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:3]:
        percentage = (commits / total_commits) * 100
        most_active_hours.append((hour, commits, percentage))

    return TimeDistribution(
        by_weekday=by_weekday,
        most_active_hours=most_active_hours,
    )
