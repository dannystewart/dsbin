from __future__ import annotations

from dataclasses import dataclass

from polykit.text import plural

from dsbin.workcalc.data import FormattedTime, WorkStats


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
            f"Total {plural(item_name, stats.total_items, with_count=True)}",
            f"Active {plural('day', stats.active_days, with_count=True)}",
            f"Average {plural(item_name, stats.total_items)} per active day: {stats.avg_items_per_day:.1f}",
            f"\nTotal work time: {formatted_time}",
        ]
