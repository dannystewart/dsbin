from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, datetime

from .sessions import calculate_session_stats, calculate_session_times, format_session_stats
from .streaks import calculate_streaks, format_streak_info
from .summary import WorkStats, calculate_summary_stats, format_summary_stats
from .time import TimeSpan, calculate_time_distribution, format_time_span

from dsutil.animation import walking_animation
from dsutil.log import LocalLogger, TimeAwareLogger

base_logger = LocalLogger.setup_logger("gitcalc", message_only=True)
logger = TimeAwareLogger(base_logger)


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


def get_dates_from_args(args: argparse.Namespace) -> tuple[date | None, date | None]:
    """Get start and end dates from command-line arguments."""
    # Parse dates and build date range string
    start_date = parse_date(args.start) if args.start else None
    end_date = parse_date(args.end) if args.end else None

    date_range_str = ""
    if start_date or end_date:
        date_range_str += "Only considering commits"
    if start_date:
        date_range_str += f" on or after {start_date:%B %-d, %Y}"
        if end_date:
            date_range_str += " and"
    if end_date:
        date_range_str += f" on or before {end_date:%B %-d, %Y}"
    if date_range_str:
        logger.info("%s.", date_range_str)

    return start_date, end_date


def parse_date(date_str: str) -> date:
    """Parse the date string provided as an argument."""
    try:
        return datetime.strptime(date_str, "%m/%d/%Y %z").date()
    except ValueError as e:
        msg = f"Invalid date format: {date_str}. Please use MM/DD/YYYY."
        raise ValueError(msg) from e


def format_hour(hour: int) -> str:
    """Format hour in 12-hour format with AM/PM."""
    if hour == 0:
        return "12 AM"
    if hour < 12:
        return f"{hour} AM"
    if hour == 12:
        return "12 PM"
    return f"{hour - 12} PM"


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


def filter_timestamps(
    timestamps: list[datetime],
    start_date: date | None,
    end_date: date | None,
    stats: WorkStats,
) -> list[datetime]:
    """Filter timestamps based on date range and collect basic stats."""
    filtered = []
    for timestamp in timestamps:
        if start_date and timestamp.date() < start_date:
            continue
        if end_date and timestamp.date() > end_date:
            continue
        filtered.append(timestamp)

        # Track hour and weekday stats
        stats.commits_by_hour[timestamp.hour] += 1
        stats.commits_by_weekday[timestamp.weekday()] += 1

        if stats.earliest_timestamp is None or timestamp < stats.earliest_timestamp:
            stats.earliest_timestamp = timestamp
        if stats.latest_timestamp is None or timestamp > stats.latest_timestamp:
            stats.latest_timestamp = timestamp

    return sorted(filtered)


def calculate_work_time(
    timestamps: list[datetime],
    max_break_time: int,
    min_work_per_commit: int,
    start_date: date | None,
    end_date: date | None,
) -> WorkStats:
    """Calculate the total work time based on commit timestamps."""
    with walking_animation("\nAnalyzing commits...", "cyan"):
        stats = WorkStats(total_commits=len(timestamps))

        if not timestamps:
            return stats

        filtered_timestamps = filter_timestamps(timestamps, start_date, end_date, stats)
        if not filtered_timestamps:
            return stats

        stats.total_time = calculate_session_times(
            filtered_timestamps,
            max_break_time,
            min_work_per_commit,
            stats,
        )

        # Calculate streak using existing calculate_streaks function
        streak_info = calculate_streaks(sorted(stats.commits_by_day.keys()))
        stats.longest_streak = (streak_info.longest_start, streak_info.longest_length)

        return stats


def print_stats(stats: WorkStats) -> None:
    """Print calculated statistics."""
    logger.info("Processed %d commits", stats.total_commits)

    # Display time span information
    if time_span := TimeSpan.from_stats(stats):
        for message in format_time_span(time_span):
            logger.debug("%s", message)

    # Display session statistics
    logger.info("\nWork patterns:")
    session_stats = calculate_session_stats(stats)
    for message in format_session_stats(session_stats):
        logger.debug("%s", message)

    # Display time distribution
    time_dist = calculate_time_distribution(stats)

    logger.info("\nDay of week patterns:")
    for day, (commits, percentage) in time_dist.by_weekday.items():
        logger.debug(
            "%s: %d commits (%.1f%%)",
            day.name.capitalize(),
            commits,
            percentage,
        )

    logger.info("\nMost active hours:")
    for hour, commits, percentage in time_dist.most_active_hours:
        logger.debug(
            "  %s: %d commits (%.1f%%)",
            format_hour(hour),
            commits,
            percentage,
        )

    # Display streak information
    print()
    streak_info = calculate_streaks(sorted(stats.commits_by_day.keys()))
    for message in format_streak_info(streak_info):
        logger.info("%s", message)

    # Display summary statistics
    print()
    summary_stats = calculate_summary_stats(stats)
    for message in format_summary_stats(summary_stats):
        logger.info("%s", message)


def main() -> None:
    """Calculate work time based on git commit timestamps."""
    args = parse_args()

    # Verify git repository
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        logger.error("Not a git repository.")
        sys.exit(1)

    start_date, end_date = get_dates_from_args(args)

    # Log calculation parameters
    logger.debug(
        "Considering %d minutes to be a session break with a minimum of %d minutes per commit.",
        args.break_time,
        args.min_work,
    )

    # Calculate base statistics
    timestamps = get_git_commits()
    stats = calculate_work_time(
        timestamps,
        args.break_time,
        args.min_work,
        start_date,
        end_date,
    )

    print_stats(stats)
