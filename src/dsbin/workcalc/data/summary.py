from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from polykit.parsers import Text

from dsbin.workcalc.data import FormattedTime

if TYPE_CHECKING:
    from datetime import date, datetime


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
    time_by_day: defaultdict[date, int] = field(default_factory=lambda: defaultdict(int))
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


@dataclass
class SummaryStats:
    """Summary statistics about work patterns."""

    total_items: int
    active_days: int
    avg_items_per_day: float
    total_time: int  # in minutes


class SummaryAnalyzer:
    """Analyzes summary statistics of work patterns."""

    @staticmethod
    def calculate_summary_stats(stats: WorkStats) -> SummaryStats:
        """Calculate summary statistics."""
        active_days = len(stats.items_by_day)
        if active_days == 0:
            return SummaryStats(
                total_items=0,
                active_days=0,
                avg_items_per_day=0,
                total_time=0,
            )

        return SummaryStats(
            total_items=stats.total_items,
            active_days=active_days,
            avg_items_per_day=stats.total_items / active_days,
            total_time=stats.total_time,
        )

    @staticmethod
    def format_summary_stats(stats: SummaryStats, item_name: str = "item") -> list[str]:
        """Format summary statistics for display."""
        formatted_time = FormattedTime.from_minutes(stats.total_time)
        return [
            f"Total {Text.plural(item_name, stats.total_items, with_count=True)}",
            f"Active {Text.plural('day', stats.active_days, with_count=True)}",
            f"Average {Text.plural(item_name, stats.total_items)} per active day: {stats.avg_items_per_day:.1f}",
            f"\nTotal work time: {formatted_time}",
        ]
