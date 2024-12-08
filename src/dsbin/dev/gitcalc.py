from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum

from dsutil import TZ
from dsutil.animation import walking_animation
from dsutil.log import LocalLogger, TimeAwareLogger

base_logger = LocalLogger.setup_logger("gitcalc", message_only=True)
logger = TimeAwareLogger(base_logger)


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
class StreakInfo:
    """Information about commit streaks."""

    longest_start: date | None = None
    longest_length: int = 0
    current_start: date | None = None
    current_length: int = 0


def parse_date(date_str: str) -> date:
    """Parse the date string provided as an argument."""
    try:
        return datetime.strptime(date_str, "%m/%d/%Y %z").date()
    except ValueError as e:
        msg = f"Invalid date format: {date_str}. Please use MM/DD/YYYY."
        raise ValueError(msg) from e


def format_date(dt: datetime) -> str:
    """Format the date without leading zero in the day."""
    return dt.strftime("%B %-d, %Y at %-I:%M %p").replace(" 0", " ")


def format_hour(hour: int) -> str:
    """Format hour in 12-hour format with AM/PM."""
    if hour == 0:
        return "12 AM"
    if hour < 12:
        return f"{hour} AM"
    if hour == 12:
        return "12 PM"
    return f"{hour - 12} PM"


def format_work_time(total_minutes: int) -> tuple[int, int, int]:
    """Convert total minutes into days, hours, and minutes."""
    days, remainder = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    return days, hours, minutes


def get_git_commits() -> list[datetime]:
    """Get timestamps of all commits in the repository."""
    try:
        result = subprocess.run(
            ["git", "log", "--format=%aI"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        msg = "Failed to get git commits. Are you in a git repository?"
        raise RuntimeError(msg) from e

    timestamps = []
    for line in result.stdout.splitlines():
        dt = datetime.fromisoformat(line.strip())
        timestamps.append(dt)

    return timestamps


def calculate_work_time(
    max_break_time: int,
    min_work_per_commit: int,
    start_date: date | None,
    end_date: date | None,
) -> WorkStats:
    """Calculate the total work time based on commit timestamps."""
    with walking_animation("\nAnalyzing commits...", "cyan"):
        timestamps = get_git_commits()
        stats = WorkStats(total_commits=len(timestamps))

        if not timestamps:
            return stats

        # Filter and sort timestamps
        filtered_timestamps = []
        for timestamp in timestamps:
            if start_date and timestamp.date() < start_date:
                continue
            if end_date and timestamp.date() > end_date:
                continue
            filtered_timestamps.append(timestamp)

            # Track hour and weekday stats for each valid commit
            stats.commits_by_hour[timestamp.hour] += 1
            stats.commits_by_weekday[timestamp.weekday()] += 1

            if stats.earliest_timestamp is None or timestamp < stats.earliest_timestamp:
                stats.earliest_timestamp = timestamp
            if stats.latest_timestamp is None or timestamp > stats.latest_timestamp:
                stats.latest_timestamp = timestamp

        if not filtered_timestamps:
            return stats

        filtered_timestamps.sort()
        total_time = 0
        last_timestamp = filtered_timestamps[0]

        # Initialize session tracking
        current_session_start = last_timestamp
        current_session_time = min_work_per_commit
        stats.commits_by_day[last_timestamp.date()] += 1

        # Add minimum work time for the first commit
        total_time += min_work_per_commit

        for timestamp in filtered_timestamps[1:]:
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
                    stats.longest_session = (current_session_start, current_session_time)
                stats.session_count += 1
                current_session_start = timestamp
                current_session_time = min_work_per_commit
                total_time += min_work_per_commit

            stats.time_by_day[timestamp.date()] += work_time
            last_timestamp = timestamp

        # Don't forget to count the last session
        stats.session_count += 1
        if current_session_time > stats.longest_session[1]:
            stats.longest_session = (current_session_start, current_session_time)

        stats.total_time = total_time

        # Calculate longest streak
        active_days = sorted(stats.commits_by_day.keys())
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

        stats.longest_streak = (longest_streak_start, longest_streak)

        return stats


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


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate work time based on git commit timestamps."
    )
    parser.add_argument(
        "-b",
        "--break-time",
        type=int,
        default=60,
        help="Max minutes before session end (default: 60)",
    )
    parser.add_argument(
        "-m",
        "--min-work",
        type=int,
        default=15,
        help="Minimum minutes of work per commit (default: 15)",
    )
    parser.add_argument(
        "--start",
        help="Start date for filtering (format: MM/DD/YYYY)",
    )
    parser.add_argument(
        "--end",
        help="End date for filtering (format: MM/DD/YYYY)",
    )
    return parser.parse_args()


def main() -> None:
    """Calculate work time based on git commit timestamps."""
    args = parse_args()
    try:  # Quick check if we're in a git repository
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        logger.error("Not a git repository.")
        sys.exit(1)

    max_break_time = args.break_time
    start_date = parse_date(args.start) if args.start else None
    end_date = parse_date(args.end) if args.end else None

    date_range_str = ""
    if start_date or end_date:
        date_range_str += "Only considering commits"
    if start_date:
        date_range_str += f" on or after {start_date.strftime('%B %-d, %Y')}"
        if end_date:
            date_range_str += " and"
    if end_date:
        date_range_str += f" on or before {end_date.strftime('%B %-d, %Y')}"
    if date_range_str:
        logger.info("%s.", date_range_str)

    logger.debug(
        "Considering %d minutes to be a session break with a minimum of %d minutes per commit.",
        max_break_time,
        args.min_work,
    )

    stats = calculate_work_time(
        args.break_time,
        args.min_work,
        start_date,
        end_date,
    )
    days, hours, minutes = format_work_time(int(stats.total_time))

    logger.info("Processed %d commits", stats.total_commits)

    if stats.earliest_timestamp and stats.latest_timestamp:
        time_span = stats.latest_timestamp - stats.earliest_timestamp
        span_days, remainder = divmod(time_span.total_seconds(), 86400)
        span_hours, remainder = divmod(remainder, 3600)
        logger.debug("First commit: %s", format_date(stats.earliest_timestamp))
        logger.debug("Last commit: %s", format_date(stats.latest_timestamp))
        logger.debug(
            "Time between first and last: %d days, %d hours",
            int(span_days),
            int(span_hours),
        )

    # Additional statistics
    logger.info("\nWork patterns:")
    logger.debug("Number of work sessions: %d", stats.session_count)

    # Most productive day by commits
    most_commits_day = max(stats.commits_by_day.items(), key=lambda x: x[1])
    logger.debug(
        "Most active day by commits: %s (%d commits)",
        most_commits_day[0].strftime("%B %-d, %Y"),
        most_commits_day[1],
    )

    # Most productive day by time
    most_time_day = max(stats.time_by_day.items(), key=lambda x: x[1])
    day_hours, day_minutes = divmod(most_time_day[1], 60)
    logger.debug(
        "Most active day by time: %s (%d hours, %d minutes)",
        most_time_day[0].strftime("%B %-d, %Y"),
        day_hours,
        day_minutes,
    )

    # Longest session
    if stats.longest_session[0]:
        session_hours, session_minutes = divmod(stats.longest_session[1], 60)
        logger.debug(
            "Longest work session: %s (%d hours, %d minutes)",
            stats.longest_session[0].strftime("%B %-d, %Y"),
            session_hours,
            session_minutes,
        )

    # Day of week stats
    logger.info("\nDay of week patterns:")
    total_commits = sum(stats.commits_by_weekday.values())
    for day in DayOfWeek:
        commits = stats.commits_by_weekday[day.value]
        percentage = (commits / total_commits) * 100
        logger.debug(
            "%s: %d commits (%.1f%%)",
            day.name.capitalize(),
            commits,
            percentage,
        )

    # Time of day stats
    most_active_hours = sorted(stats.commits_by_hour.items(), key=lambda x: x[1], reverse=True)[:3]
    logger.info("\nMost active hours:")
    for hour, commits in most_active_hours:
        percentage = (commits / total_commits) * 100
        logger.debug(
            "  %s: %d commits (%.1f%%)",
            format_hour(hour),
            commits,
            percentage,
        )

    # Calculate and display streaks
    print()
    streak_info = calculate_streaks(sorted(stats.commits_by_day.keys()))
    for message in format_streak_info(streak_info):
        logger.info("%s", message)

    # Average commits per day
    active_days = len(stats.commits_by_day)
    avg_commits = stats.total_commits / active_days
    logger.info("Average commits per active day: %.1f", avg_commits)

    days_str = f"{days} day{'' if days == 1 else 's'}, " if days else ""
    logger.info("\nTotal work time: %s%d hours, %d minutes", days_str, hours, minutes)
