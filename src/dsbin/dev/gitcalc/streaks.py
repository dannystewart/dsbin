from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from dsutil import TZ


@dataclass
class StreakInfo:
    """Information about commit streaks."""

    longest_start: date | None = None
    longest_length: int = 0
    current_start: date | None = None
    current_length: int = 0


class StreakAnalyzer:
    """Class to analyze commit streaks."""

    @staticmethod
    def calculate_streaks(active_days: list[date]) -> StreakInfo:
        """Calculate longest and current streaks from active days."""
        if not active_days:
            return StreakInfo()

        streaks = StreakInfo()
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

        streaks.longest_start = longest_streak_start
        streaks.longest_length = longest_streak

        return streaks

    @staticmethod
    def format_streak_info(streak_info: StreakInfo) -> list[str]:
        """Format streak information for display."""
        messages = []

        if streak_info.longest_start:
            streak_end = streak_info.longest_start + timedelta(days=streak_info.longest_length - 1)
            messages.append(
                f"Longest streak: {streak_info.longest_length} days "
                f"({streak_info.longest_start:%B %-d, %Y} to {streak_end:%B %-d, %Y})"
            )

        if streak_info.current_length > 0:
            messages.append(
                f"Current streak: {streak_info.current_length} days "
                f"(since {streak_info.current_start:%B %-d, %Y})"
            )

        return messages
