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
        return [
            f"[bold cyan]Total:[/bold cyan] {stats.total_items:,} [dim]{plural(item_name, stats.total_items, show_num=False)}[/dim]",
            f"[bold cyan]Active:[/bold cyan] {stats.active_days:,} [dim]{plural('active day', stats.active_days, show_num=False)}[/dim]",
            f"[bold cyan]Average:[/bold cyan] {stats.avg_items_per_day:,.1f} [dim]{plural(item_name, stats.total_items, show_num=False)} per active day[/dim]",
        ]

    @staticmethod
    def format_total_work_time(stats: SummaryStats) -> str:
        """Format total work time for display."""
        return str(FormattedTime.from_minutes(stats.total_time))
