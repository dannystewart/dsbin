from __future__ import annotations

import operator
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


@dataclass
class ActiveDaysStats:
    """Statistics about active vs inactive days."""

    total_days: int
    active_days: int
    inactive_days: int
    active_percentage: float
    inactive_percentage: float


class TimeAnalyzer:
    """Class to analyze time-related statistics."""

    @staticmethod
    def format_date(dt: datetime) -> str:
        """Format the date without leading zero in the day."""
        return dt.strftime("%B %-d, %Y at %-I:%M %p").replace(" 0", " ")

    @staticmethod
    def format_time_span(span: TimeSpan) -> list[str]:
        """Format time span information for display."""
        return [
            f"First commit: {TimeAnalyzer.format_date(span.first_commit)}",
            f"Last commit: {TimeAnalyzer.format_date(span.last_commit)}",
            f"Time between first and last: {span.span_days} days, {span.span_hours} hours",
        ]

    @staticmethod
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
            key=operator.itemgetter(1),
            reverse=True,
        )[:3]:
            percentage = (commits / total_commits) * 100
            most_active_hours.append((hour, commits, percentage))

        return TimeDistribution(
            by_weekday=by_weekday,
            most_active_hours=most_active_hours,
        )

    @staticmethod
    def calculate_active_days(stats: WorkStats) -> ActiveDaysStats | None:
        """Create ActiveDaysStats from WorkStats."""
        if not (stats.earliest_timestamp and stats.latest_timestamp):
            return None

        start_date = stats.earliest_timestamp.date()
        end_date = stats.latest_timestamp.date()
        total_days = (end_date - start_date).days + 1
        active_days = len(stats.commits_by_day)
        inactive_days = total_days - active_days

        return ActiveDaysStats(
            total_days=total_days,
            active_days=active_days,
            inactive_days=inactive_days,
            active_percentage=(active_days / total_days) * 100,
            inactive_percentage=(inactive_days / total_days) * 100,
        )

    @staticmethod
    def format_active_days_stats(stats: ActiveDaysStats) -> list[str]:
        """Format active days statistics for display."""
        return [
            f"Days with commits: {stats.active_days} ({stats.active_percentage:.1f}%)",
            f"Days without commits: {stats.inactive_days} ({stats.inactive_percentage:.1f}%)",
        ]
