"""Estimate time working on a Logic project by bounce timestamps."""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from dataclasses import dataclass

from dsutil.animation import walking_animation
from dsutil.files import list_files
from dsutil.log import LocalLogger, TimeAwareLogger
from dsutil.macos import get_timestamps
from dsutil.shell import handle_keyboard_interrupt
from dsutil.tz import TZ

base_logger = LocalLogger.setup_logger("calcbounce", message_only=True)
logger = TimeAwareLogger(base_logger)


@dataclass
class WorkStats:
    """Dataclass to store calculated work statistics."""

    total_files: int = 0
    valid_files: int = 0
    total_time: int = 0
    earliest_timestamp: datetime.datetime | None = None
    latest_timestamp: datetime.datetime | None = None


def parse_timestamp(timestamp: str) -> datetime.datetime:
    """Parse the timestamp string returned by get_timestamps."""
    formats = [
        "%m/%d/%Y %I:%M:%S %p",  # Original expected format
        "%m/%d/%Y %H:%M:%S",  # 24-hour format without AM/PM
    ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(timestamp, fmt)  # noqa: DTZ007
            return dt.replace(tzinfo=TZ)
        except ValueError:
            continue

    msg = f"Unable to parse timestamp: {timestamp}"
    raise ValueError(msg)


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


def calculate_work_time(
    directory: str,
    max_break_time: int,
    recursive: bool,
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> WorkStats:
    """
    Calculate the total work time based on file creation timestamps.

    Args:
        directory: Path to the directory containing audio files.
        max_break_time: Maximum time in minutes between bounces to be considered continuous work.
        recursive: Whether to search for files recursively.
        start_date: Start date for filtering (inclusive).
        end_date: End date for filtering (inclusive).

    Returns:
        WorkStats object containing calculated statistics.
    """
    with walking_animation("\nAnalyzing files...", "cyan"):
        audio_files = list_files(
            directory,
            extensions=["wav", "m4a"],
            recursive=recursive,
            sort_key=lambda x: x.stat().st_mtime,
        )
        stats = WorkStats(total_files=len(audio_files))

        timestamps = []
        for file in audio_files:
            try:
                ctime, _ = get_timestamps(os.path.join(directory, file))
                timestamp = parse_timestamp(ctime)

                # Apply date filtering
                if start_date and timestamp.date() < start_date:
                    continue
                if end_date and timestamp.date() > end_date:
                    continue

                timestamps.append(timestamp)
                stats.valid_files += 1

                if stats.earliest_timestamp is None or timestamp < stats.earliest_timestamp:
                    stats.earliest_timestamp = timestamp
                if stats.latest_timestamp is None or timestamp > stats.latest_timestamp:
                    stats.latest_timestamp = timestamp
            except ValueError as e:
                logger.error("Could not parse timestamp for file %s: %s", file, str(e))
                continue

        if not timestamps:
            return stats

        timestamps.sort()
        total_time = 0
        last_timestamp = timestamps[0]

        for timestamp in timestamps[1:]:
            time_diff = (timestamp - last_timestamp).total_seconds() / 60
            total_time += min(time_diff, max_break_time)
            last_timestamp = timestamp

        stats.total_time = total_time

        return stats


@handle_keyboard_interrupt()
def main() -> None:
    """Calculate work time based on audio file timestamps."""
    parser = argparse.ArgumentParser(
        description="Calculate work time based on audio file timestamps."
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=".",
        help="Directory containing audio files (default: current directory)",
    )
    parser.add_argument(
        "-b",
        "--break-time",
        type=int,
        default=60,
        help="Max minutes before session end (default: 60)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search for audio files recursively",
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

    directory = os.path.abspath(args.directory)
    max_break_time = args.break_time
    recursive = args.recursive

    start_date = parse_date(args.start) if args.start else None
    end_date = parse_date(args.end) if args.end else None

    if not os.path.isdir(directory):
        logger.error("'%s' is not a valid directory.", directory)
        sys.exit(1)

    logger.info("Analyzing directory%s: %s", " recursively" if recursive else "", directory)

    date_range_str = ""
    if start_date or end_date:
        date_range_str += "Only considering files created"
    if start_date:
        date_range_str += f" on or after {start_date.strftime('%B %-d, %Y')}"
        if end_date:
            date_range_str += " and"
    if end_date:
        date_range_str += f" on or before {end_date.strftime('%B %-d, %Y')}"
    if date_range_str:
        logger.info("%s.", date_range_str)

    logger.debug("Considering %d minutes to be a session break.", max_break_time)

    stats = calculate_work_time(directory, max_break_time, recursive, start_date, end_date)
    total_work_hours = stats.total_time / 60
    work_hours = int(total_work_hours)
    work_minutes = int((total_work_hours - work_hours) * 60)

    logger.info(
        "Processed %d files%s",
        stats.total_files,
        f" ({stats.valid_files} within specified range)"
        if stats.valid_files < stats.total_files
        else "",
    )

    if stats.earliest_timestamp and stats.latest_timestamp:
        time_span = stats.latest_timestamp - stats.earliest_timestamp
        span_days, remainder = divmod(time_span.total_seconds(), 86400)
        span_hours, remainder = divmod(remainder, 3600)
        logger.debug("Oldest bounce: %s", format_date(stats.earliest_timestamp))
        logger.debug("Newest bounce: %s", format_date(stats.latest_timestamp))
        logger.debug(
            "Time between oldest and newest: %d days, %d hours",
            int(span_days),
            int(span_hours),
        )

    logger.info("\nTotal work time: %d hours, %d minutes", work_hours, work_minutes)
