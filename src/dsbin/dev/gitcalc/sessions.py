from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date, datetime

    from .summary import WorkStats


@dataclass
class SessionStats:
    """Statistics about work sessions."""

    count: int
    longest_session: tuple[datetime | None, int]
    most_active_day_commits: tuple[date, int]
    most_active_day_time: tuple[date, int]


def calculate_session_stats(stats: WorkStats) -> SessionStats:
    """Calculate statistics about work sessions."""
    most_commits_day = max(stats.commits_by_day.items(), key=lambda x: x[1])
    most_time_day = max(stats.time_by_day.items(), key=lambda x: x[1])

    return SessionStats(
        count=stats.session_count,
        longest_session=stats.longest_session,
        most_active_day_commits=most_commits_day,
        most_active_day_time=most_time_day,
    )


def calculate_session_times(
    timestamps: list[datetime],
    max_break_time: int,
    min_work_per_commit: int,
    stats: WorkStats,
) -> int:
    """Calculate session times and total work time."""
    if not timestamps:
        return 0

    total_time = min_work_per_commit  # First commit
    last_timestamp = timestamps[0]
    current_session_start = last_timestamp
    current_session_time = min_work_per_commit
    stats.commits_by_day[last_timestamp.date()] += 1

    for timestamp in timestamps[1:]:
        time_diff = (timestamp - last_timestamp).total_seconds() / 60
        stats.commits_by_day[timestamp.date()] += 1

        if time_diff <= max_break_time:
            # Same session
            work_time = max(time_diff, min_work_per_commit)
            total_time += work_time
            current_session_time += work_time
        else:
            # New session
            if current_session_time > stats.longest_session[1]:
                stats.longest_session = (current_session_start, int(current_session_time))
            stats.session_count += 1
            current_session_start = timestamp
            current_session_time = min_work_per_commit
            total_time += min_work_per_commit

        stats.time_by_day[timestamp.date()] += work_time
        last_timestamp = timestamp

    # Handle last session
    stats.session_count += 1
    if current_session_time > stats.longest_session[1]:
        stats.longest_session = (current_session_start, int(current_session_time))

    return int(total_time)


def format_session_stats(stats: SessionStats) -> list[str]:
    """Format session statistics for display."""
    messages = [
        f"Number of work sessions: {stats.count}",
        f"Most active day by commits: {stats.most_active_day_commits[0]:%B %-d, %Y} ({stats.most_active_day_commits[1]} commits)",
    ]

    day_hours, day_minutes = divmod(round(stats.most_active_day_time[1]), 60)
    messages.append(
        f"Most active day by time: {stats.most_active_day_time[0]:%B %-d, %Y} ({day_hours:.0f} hours, {day_minutes:.0f} minutes)"
    )

    if stats.longest_session[0]:
        session_hours, session_minutes = divmod(round(stats.longest_session[1]), 60)
        messages.append(
            f"Longest work session: {stats.longest_session[0]:%B %-d, %Y} ({session_hours:.0f} hours, {session_minutes:.0f} minutes)"
        )

    return messages
