from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from dataclasses import dataclass

from dsutil.animation import walking_animation
from dsutil.log import LocalLogger, TimeAwareLogger

base_logger = LocalLogger.setup_logger("gitcalc", message_only=True)
logger = TimeAwareLogger(base_logger)


@dataclass
class WorkStats:
    """Dataclass to store calculated work statistics."""

    total_commits: int = 0
    total_time: int = 0
    earliest_timestamp: datetime.datetime | None = None
    latest_timestamp: datetime.datetime | None = None


def parse_date(date_str: str) -> datetime.date:
    """Parse the date string provided as an argument."""
    try:
        return datetime.datetime.strptime(date_str, "%m/%d/%Y").date()  # noqa: DTZ007
    except ValueError as e:
        msg = f"Invalid date format: {date_str}. Please use MM/DD/YYYY."
        raise ValueError(msg) from e


def format_date(dt: datetime.datetime) -> str:
    """Format the date without leading zero in the day."""
    return dt.strftime("%B %-d, %Y at %-I:%M %p").replace(" 0", " ")


def format_work_time(total_minutes: int) -> tuple[int, int, int]:
    """Convert total minutes into days, hours, and minutes."""
    days, remainder = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    return days, hours, minutes


def get_git_commits() -> list[datetime.datetime]:
    """Get timestamps of all commits in the repository."""
    try:
        # %aI gives us ISO 8601-like format with timezone information
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
        # datetime.fromisoformat handles the ISO format including timezone
        dt = datetime.datetime.fromisoformat(line.strip())
        timestamps.append(dt)

    return timestamps


def calculate_work_time(
    max_break_time: int,
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> WorkStats:
    """Calculate the total work time based on commit timestamps."""
    with walking_animation("\nAnalyzing commits...", "cyan"):
        timestamps = get_git_commits()
        stats = WorkStats(total_commits=len(timestamps))

        if not timestamps:
            return stats

        # Filter by date if specified
        filtered_timestamps = []
        for timestamp in timestamps:
            if start_date and timestamp.date() < start_date:
                continue
            if end_date and timestamp.date() > end_date:
                continue
            filtered_timestamps.append(timestamp)

            if stats.earliest_timestamp is None or timestamp < stats.earliest_timestamp:
                stats.earliest_timestamp = timestamp
            if stats.latest_timestamp is None or timestamp > stats.latest_timestamp:
                stats.latest_timestamp = timestamp

        if not filtered_timestamps:
            return stats

        filtered_timestamps.sort()
        total_time = 0
        last_timestamp = filtered_timestamps[0]

        for timestamp in filtered_timestamps[1:]:
            time_diff = (timestamp - last_timestamp).total_seconds() / 60
            total_time += min(time_diff, max_break_time)
            last_timestamp = timestamp

        stats.total_time = total_time
        return stats


def main() -> None:
    """Calculate work time based on git commit timestamps."""
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
        "--start",
        help="Start date for filtering (format: MM/DD/YYYY)",
    )
    parser.add_argument(
        "--end",
        help="End date for filtering (format: MM/DD/YYYY)",
    )
    args = parser.parse_args()

    try:
        # Quick check if we're in a git repository
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

    logger.debug("Considering %d minutes to be a session break.", max_break_time)

    stats = calculate_work_time(max_break_time, start_date, end_date)
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

    logger.info("\nTotal work time: %d days, %d hours, %d minutes", days, hours, minutes)
