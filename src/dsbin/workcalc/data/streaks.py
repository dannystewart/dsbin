from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from polykit.parsers import TZ, Text

if TYPE_CHECKING:
    from datetime import date

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
class StreakStats:
    """Information about work streaks."""

    longest_start: date | None = None
    longest_length: int = 0
    current_start: date | None = None
    current_length: int = 0
    today_completed: bool = False


class StreakAnalyzer:
    """Analyzes streaks in work patterns."""

    @staticmethod
    def calculate_streaks(stats: WorkStats) -> StreakStats:
        """Calculate streak statistics from work stats."""
        active_days = sorted(stats.items_by_day.keys())
        if not active_days:
            return StreakStats()

        streaks = StreakStats()
        current_streak = 1
        current_streak_start = active_days[0]
        longest_streak = 1
        longest_streak_start = active_days[0]

        for i in range(1, len(active_days)):
            if (active_days[i] - active_days[i - 1]).days == 1:
                current_streak += 1
                if current_streak > longest_streak:
                    longest_streak = current_streak
                    longest_streak_start = current_streak_start
            else:
                current_streak = 1
                current_streak_start = active_days[i]

        # Check if we're currently in a streak
        today = datetime.now(tz=TZ).date()
        last_active = active_days[-1]
        days_since_last = (today - last_active).days

        if days_since_last <= 1:  # Consider today and yesterday as continuing the streak
            streaks.current_start = current_streak_start
            streaks.current_length = current_streak
            streaks.today_completed = last_active == today

        streaks.longest_start = longest_streak_start
        streaks.longest_length = longest_streak

        return streaks

    @staticmethod
    def format_streak_stats(stats: StreakStats, item_name: str = "work") -> list[str]:
        """Format streak information for display."""
        messages = []

        if stats.longest_start:
            streak_end = stats.longest_start + timedelta(days=stats.longest_length - 1)
            messages.append(
                f"Longest {item_name} streak: {Text.plural('day', stats.longest_length, with_count=True)} "
                f"({stats.longest_start:%B %-d, %Y} to {streak_end:%B %-d, %Y})"
            )

        if stats.current_length > 0:
            post_status = "including today" if stats.today_completed else "• not completed today"
            messages.append(
                f"Current {item_name} streak: {Text.plural('day', stats.current_length, with_count=True)} "
                f"(since {stats.current_start:%B %-d, %Y}) {post_status}"
            )

        return messages
