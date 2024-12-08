from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
        days_str = f"{self.days} day{'' if self.days == 1 else 's'}, " if self.days else ""
        return f"{days_str}{self.hours} hours, {self.minutes} minutes ({self.total_hours} hours)"


@dataclass
class WorkStats:
    """Dataclass to store calculated work statistics."""

    total_commits: int = 0
    total_time: int = 0
    earliest_timestamp: datetime | None = None
    latest_timestamp: datetime | None = None
    session_count: int = 0
    commits_by_day: defaultdict[date, int] = field(default_factory=lambda: defaultdict(int))
    commits_by_hour: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    commits_by_weekday: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    time_by_day: defaultdict[date, int] = field(default_factory=lambda: defaultdict(int))
    longest_session: tuple[datetime | None, int] = field(default_factory=lambda: (None, 0))
    longest_streak: tuple[date | None, int] = field(default_factory=lambda: (None, 0))


@dataclass
class SummaryStats:
    """Summary statistics about the repository."""

    total_commits: int
    active_days: int
    avg_commits_per_day: float
    total_time: int  # in minutes


def calculate_summary_stats(stats: WorkStats) -> SummaryStats:
    """Calculate summary statistics."""
    active_days = len(stats.commits_by_day)
    return SummaryStats(
        total_commits=stats.total_commits,
        active_days=active_days,
        avg_commits_per_day=stats.total_commits / active_days,
        total_time=stats.total_time,
    )


def format_summary_stats(stats: SummaryStats) -> list[str]:
    """Format summary statistics for display."""
    formatted_time = FormattedTime.from_minutes(stats.total_time)
    return [
        f"Average commits per active day: {stats.avg_commits_per_day:.1f}",
        f"Total work time: {formatted_time}",
    ]
