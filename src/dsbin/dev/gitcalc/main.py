from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, datetime

from .sessions import SessionAnalyzer
from .streaks import StreakAnalyzer
from .summary import SummaryAnalyzer, WorkStats
from .time import TimeAnalyzer, TimeSpan

from dsutil.animation import walking_animation
from dsutil.log import LocalLogger, TimeAwareLogger
from dsutil.tools import configure_traceback

configure_traceback()


class GitCalculator:
    """Class to calculate work time based on git commit timestamps."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.break_time = args.break_time
        self.min_work = args.min_work

        self.base_logger = LocalLogger.setup_logger("gitcalc", message_only=True)
        self.logger = TimeAwareLogger(self.base_logger)

        self.start_date = self.parse_date(args.start) if args.start else None
        self.end_date = self.parse_date(args.end) if args.end else None

        self.verify_git_repository()
        self.get_run_dates()
        self.log_details()

        self.timestamps = self.get_git_commits()
        self.total_commits = len(self.timestamps)

        with walking_animation("\nAnalyzing commits...", "cyan"):
            self.stats = WorkStats(total_commits=self.total_commits)
            self.filtered_timestamps = self.filter_timestamps()

            # Initialize analyzers
            self.sessions = SessionAnalyzer()
            self.streaks = StreakAnalyzer()
            self.summary = SummaryAnalyzer()
            self.time = TimeAnalyzer()

            # Calculate work time before printing stats
            self.calculate_work_time()

        # Print stats after all calculations are complete
        self.print_stats()

    def verify_git_repository(self) -> None:
        """Verify that the current directory is a git repository."""
        # Verify git repository
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            self.logger.error("Not a git repository.")
            sys.exit(1)

    def get_run_dates(self) -> None:
        """Get start and end dates from command-line arguments."""
        # Parse dates and build date range string
        date_range_str = ""
        if self.start_date or self.end_date:
            date_range_str += "Only considering commits"
        if self.start_date:
            date_range_str += f" on or after {self.start_date:%B %-d, %Y}"
            if self.end_date:
                date_range_str += " and"
        if self.end_date:
            date_range_str += f" on or before {self.end_date:%B %-d, %Y}"
        if date_range_str:
            self.logger.info("%s.", date_range_str)

    def log_details(self) -> None:
        """Log the calculation based on the provided arguments."""
        self.logger.debug(
            "Considering %d minutes to be a session break with a minimum of %d minutes per commit.",
            self.break_time,
            self.min_work,
        )

    def get_git_commits(self) -> list[datetime]:
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

    def filter_timestamps(self) -> list[datetime]:
        """Filter timestamps based on date range and collect basic stats."""
        filtered = []
        for timestamp in self.timestamps:
            if self.start_date and timestamp.date() < self.start_date:
                continue
            if self.end_date and timestamp.date() > self.end_date:
                continue
            filtered.append(timestamp)

            # Track hour and weekday stats
            self.stats.commits_by_hour[timestamp.hour] += 1
            self.stats.commits_by_weekday[timestamp.weekday()] += 1

            if self.stats.earliest_timestamp is None or timestamp < self.stats.earliest_timestamp:
                self.stats.earliest_timestamp = timestamp
            if self.stats.latest_timestamp is None or timestamp > self.stats.latest_timestamp:
                self.stats.latest_timestamp = timestamp

        return sorted(filtered)

    def calculate_work_time(self) -> None:
        """Calculate the total work time based on commit timestamps."""

        if not self.timestamps or not self.filtered_timestamps:
            return

        self.stats.total_time = self.sessions.calculate_session_times(
            self.filtered_timestamps,
            self.break_time,
            self.min_work,
            self.stats,
        )

        # Calculate streak using existing calculate_streaks function
        streak_info = self.streaks.calculate_streaks(sorted(self.stats.commits_by_day.keys()))
        self.stats.longest_streak = (streak_info.longest_start, streak_info.longest_length)

    def print_stats(self) -> None:
        """Print calculated statistics."""
        self.logger.info("Processed %d commits", self.stats.total_commits)

        # Display time span information
        if time_span := TimeSpan.from_stats(self.stats):
            for message in self.time.format_time_span(time_span):
                self.logger.debug("%s", message)

        # Display active days information
        if active_days_stats := self.time.calculate_active_days(self.stats):
            for message in self.time.format_active_days_stats(active_days_stats):
                self.logger.debug("%s", message)

        # Display session statistics
        self.logger.info("\nWork patterns:")
        session_stats = self.sessions.calculate_session_stats(self.stats)
        for message in self.sessions.format_session_stats(session_stats):
            self.logger.debug("%s", message)

        # Display time distribution
        time_dist = self.time.calculate_time_distribution(self.stats)

        self.logger.info("\nDay of week patterns:")
        for day, (commits, percentage) in time_dist.by_weekday.items():
            self.logger.debug(
                "%s: %d commits (%.1f%%)",
                day.name.capitalize(),
                commits,
                percentage,
            )

        self.logger.info("\nMost active hours:")
        for hour, commits, percentage in time_dist.most_active_hours:
            self.logger.debug(
                "  %s: %d commits (%.1f%%)",
                self.format_hour(hour),
                commits,
                percentage,
            )

        # Display streak information
        print()
        streak_info = self.streaks.calculate_streaks(sorted(self.stats.commits_by_day.keys()))
        for message in self.streaks.format_streak_info(streak_info):
            self.logger.info("%s", message)

        # Display summary statistics
        print()
        summary_stats = self.summary.calculate_summary_stats(self.stats)
        for message in self.summary.format_summary_stats(summary_stats):
            self.logger.info("%s", message)

    @staticmethod
    def parse_date(date_str: str) -> date:
        """Parse the date string provided as an argument."""
        try:
            return datetime.strptime(date_str, "%m/%d/%Y %z").date()
        except ValueError as e:
            msg = f"Invalid date format: {date_str}. Please use MM/DD/YYYY."
            raise ValueError(msg) from e

    @staticmethod
    def format_hour(hour: int) -> str:
        """Format hour in 12-hour format with AM/PM."""
        if hour == 0:
            return "12 AM"
        if hour < 12:
            return f"{hour} AM"
        if hour == 12:
            return "12 PM"
        return f"{hour - 12} PM"


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
    GitCalculator(args)
