from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from polykit.formatters import Text

if TYPE_CHECKING:
    from datetime import date, datetime

    from dsbin.workcalc.data import WorkStats


@dataclass
class SessionStats:
    """Statistics about work sessions."""

    count: int
    longest_session: tuple[datetime | None, int]
    most_active_day_items: tuple[date, int]  # Changed from commits to items
    most_active_day_time: tuple[date, int | float]


class SessionAnalyzer:
    """Class to analyze work sessions."""

    @staticmethod
    def calculate_session_stats(stats: WorkStats) -> SessionStats:
        """Calculate statistics about work sessions."""
        most_items_day = max(stats.items_by_day.items(), key=operator.itemgetter(1))
        most_time_day = max(stats.time_by_day.items(), key=operator.itemgetter(1))

        return SessionStats(
            count=stats.session_count,
            longest_session=stats.longest_session,
            most_active_day_items=most_items_day,
            most_active_day_time=most_time_day,
        )

    @staticmethod
    def format_session_stats(stats: SessionStats, item_name: str = "item") -> list[str]:
        """Format session statistics for display."""
        messages = [
            f"Number of work sessions: {stats.count}",
            f"Most active day by {Text.plural(item_name, stats.most_active_day_items[1])}: "
            f"{stats.most_active_day_items[0]:%B %-d, %Y} "
            f"({Text.plural(item_name, stats.most_active_day_items[1], with_count=True)})",
        ]

        day_hours, day_minutes = divmod(round(stats.most_active_day_time[1]), 60)
        messages.append(
            f"Most active day by time: {stats.most_active_day_time[0]:%B %-d, %Y} "
            f"({Text.plural('hour', day_hours, with_count=True)}, "
            f"{Text.plural('minute', day_minutes, with_count=True)})"
        )

        if stats.longest_session[0]:
            session_hours, session_minutes = divmod(round(stats.longest_session[1]), 60)
            messages.append(
                f"Longest work session: {stats.longest_session[0]:%B %-d, %Y} "
                f"({Text.plural('hour', session_hours, with_count=True)}, "
                f"{Text.plural('minute', session_minutes, with_count=True)})"
            )

        return messages
