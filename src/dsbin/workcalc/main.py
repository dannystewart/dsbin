"""Calculate how much time went into a project."""

from __future__ import annotations

import argparse
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from logician import Logician
from polykit import polykit_setup
from polykit.parsers import Text
from walking_man import walking_man

from dsbin.workcalc.data import (
    SessionAnalyzer,
    StreakAnalyzer,
    SummaryAnalyzer,
    TimeAnalyzer,
    TimeSpan,
    WorkStats,
)
from dsbin.workcalc.plugins import BounceDataSource, GitDataSource

if TYPE_CHECKING:
    from datetime import date

    from dsbin.workcalc import DataSourcePlugin
    from dsbin.workcalc.data import WorkItem

polykit_setup()


def parse_date(date_str: str) -> datetime.date:
    """Parse the date string provided as an argument.

    Raises:
        ValueError: If the date can't be parsed.
    """
    try:
        return datetime.datetime.strptime(date_str, "%m/%d/%Y").date()  # noqa: DTZ007
    except ValueError as e:
        msg = f"Invalid date format: {date_str}. Please use MM/DD/YYYY."
        raise ValueError(msg) from e


@dataclass
class WorkAnalysisConfig:
    """Configuration for work analysis."""

    break_time: int = 60  # minutes
    min_work_per_item: int = 15  # minutes
    start_date: date | None = None
    end_date: date | None = None


class WorkCalculator:
    """Generic work pattern analyzer."""

    def __init__(self, data_source: DataSourcePlugin, config: WorkAnalysisConfig) -> None:
        """Initialize the calculator with a data source and configuration.

        Raises:
            ValueError: If the data source is invalid.
        """
        self.data_source = data_source
        self.config = config
        self.item_name = self._get_item_name()

        self.logger = Logician.get_logger("workcalc", level="debug", simple=True, time_aware=True)

        if not self.data_source.validate_source():
            msg = f"Invalid {self.data_source.source_name} data source"
            raise ValueError(msg)

        # Log configuration details
        self.logger.debug(
            "Considering %s to be a session break with a minimum of %s per %s.",
            Text.plural("minute", self.config.break_time, with_count=True),
            Text.plural("minute", self.config.min_work_per_item, with_count=True),
            self.item_name,
        )

        self.stats = WorkStats(source_type=self.data_source.source_name)

        # Initialize analyzers
        self.session_analyzer = SessionAnalyzer()
        self.streak_analyzer = StreakAnalyzer()
        self.summary_analyzer = SummaryAnalyzer()
        self.time_analyzer = TimeAnalyzer()

        with walking_man(
            f"\nAnalyzing {self.data_source.source_name.capitalize()} data...", "cyan"
        ):
            self.work_items = self.collect_work_items()
            self.analyze_work_patterns()

    def _get_item_name(self) -> str:
        """Get the appropriate name for work items based on source type."""
        return {
            "git": "commit",
            "logic": "bounce",
        }.get(self.data_source.source_name, "item")

    def analyze(self) -> None:
        """Run analysis and display results."""
        self.logger.info("Processed %d %ss", self.stats.total_items, self.item_name)

        # Display time span information
        if time_span := TimeSpan.from_stats(self.stats):
            for message in self.time_analyzer.format_time_span(time_span, self.item_name):
                self.logger.debug("%s", message)

        # Display session statistics
        self.logger.info("\nWork patterns:")
        session_stats = self.session_analyzer.calculate_session_stats(self.stats)
        for message in self.session_analyzer.format_session_stats(session_stats, self.item_name):
            self.logger.debug("%s", message)

        # Display time distribution
        time_dist = self.time_analyzer.calculate_time_distribution(self.stats)

        self.logger.info("\nDay of week patterns:")
        for message in self.time_analyzer.format_distribution(time_dist, self.item_name):
            self.logger.debug("%s", message)

        # Display streak information
        print()  # Add spacing
        streak_stats = self.streak_analyzer.calculate_streaks(self.stats)
        for message in self.streak_analyzer.format_streak_stats(streak_stats, self.item_name):
            self.logger.info("%s", message)

        # Display summary statistics
        print()  # Add spacing
        summary_stats = self.summary_analyzer.calculate_summary_stats(self.stats)
        for message in self.summary_analyzer.format_summary_stats(summary_stats, self.item_name):
            self.logger.info("%s", message)

    def collect_work_items(self) -> list[WorkItem]:
        """Collect and filter work items from the data source."""
        items = []
        for item in self.data_source.get_work_items():
            if self.config.start_date and item.timestamp.date() < self.config.start_date:
                continue
            if self.config.end_date and item.timestamp.date() > self.config.end_date:
                continue

            items.append(item)
            self.stats.total_items += 1
            self.stats.update_timestamp_stats(item.timestamp)

        return sorted(items, key=lambda x: x.timestamp)

    def analyze_work_patterns(self) -> None:
        """Analyze work patterns in the collected items."""
        if not self.work_items:
            return

        self.calculate_session_times()

    def calculate_session_times(self) -> None:
        """Calculate session times and work patterns."""
        if not self.work_items:
            return

        total_time = self.config.min_work_per_item  # First item
        work_time = total_time
        last_timestamp = self.work_items[0].timestamp
        current_session_start = last_timestamp
        current_session_time = self.config.min_work_per_item

        for item in self.work_items[1:]:
            time_diff = (item.timestamp - last_timestamp).total_seconds() / 60

            if time_diff <= self.config.break_time:
                # Same session
                work_time = max(time_diff, self.config.min_work_per_item)
                total_time += work_time
                current_session_time += work_time
            else:
                # New session
                if current_session_time > self.stats.longest_session[1]:
                    self.stats.longest_session = (current_session_start, int(current_session_time))
                self.stats.session_count += 1
                current_session_start = item.timestamp
                current_session_time = self.config.min_work_per_item
                total_time += self.config.min_work_per_item

            self.stats.time_by_day[item.timestamp.date()] += work_time
            last_timestamp = item.timestamp

        # Handle last session
        self.stats.session_count += 1
        if current_session_time > self.stats.longest_session[1]:
            self.stats.longest_session = (current_session_start, int(current_session_time))

        self.stats.total_time = int(total_time)


def main() -> None:
    """Calculate work patterns from various data sources."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="source_type", required=True)

    # Git repository parser
    git_parser = subparsers.add_parser("git")
    git_parser.add_argument("repo_path", type=Path)

    # Logic bounce parser
    bounce_parser = subparsers.add_parser("logic")
    bounce_parser.add_argument("directory", type=Path)

    # Common arguments
    for p in [git_parser, bounce_parser]:
        p.add_argument("-b", "--break-time", type=int, default=60)
        p.add_argument("-m", "--min-work", type=int, default=15)
        p.add_argument("--start", help="Start date (MM/DD/YYYY)")
        p.add_argument("--end", help="End date (MM/DD/YYYY)")

    args = parser.parse_args()

    config = WorkAnalysisConfig(
        break_time=args.break_time,
        min_work_per_item=args.min_work,
        start_date=parse_date(args.start) if args.start else None,
        end_date=parse_date(args.end) if args.end else None,
    )

    data_source: DataSourcePlugin
    if args.source_type == "git":
        data_source = GitDataSource(args.repo_path)
    elif args.source_type == "logic":
        data_source = BounceDataSource(args.directory)

    calculator = WorkCalculator(data_source, config)
    calculator.analyze()
