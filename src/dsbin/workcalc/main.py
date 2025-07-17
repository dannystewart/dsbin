"""Calculate how much time went into a project."""

from __future__ import annotations

import argparse
import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING

from polykit import TZ
from polykit.cli import walking_man
from polykit.core import polykit_setup
from polykit.text import plural
from rich.console import Console

from dsbin.workcalc import PluginRegistry
from dsbin.workcalc.data import (
    SessionAnalyzer,
    StreakAnalyzer,
    SummaryAnalyzer,
    TimeAnalyzer,
    TimeSpan,
    WorkStats,
)
from dsbin.workcalc.plugins import initialize_plugins

if TYPE_CHECKING:
    from datetime import date

    from dsbin.workcalc import DataSourcePlugin
    from dsbin.workcalc.data import WorkItem

polykit_setup()
console = Console(highlight=False)


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

        if not self.data_source.validate_source():
            msg = f"Invalid {self.data_source.source_name} data source"
            raise ValueError(msg)

        # Log configuration details
        console.print(
            f"Considering [bold]{plural('minute', self.config.break_time)}[/bold] to be a session break with a minimum of "
            f"[bold]{plural('minute', self.config.min_work_per_item)}[/bold] per {self.data_source.item_name}.",
            style="dim",
        )

        self.stats = WorkStats(source_type=self.data_source.source_name)

        # Initialize analyzers
        self.session_analyzer = SessionAnalyzer()
        self.streak_analyzer = StreakAnalyzer()
        self.summary_analyzer = SummaryAnalyzer()
        self.time_analyzer = TimeAnalyzer()

        with walking_man(
            f"\nAnalyzing {self.data_source.source_name.capitalize()} data...", "blue"
        ):
            self.work_items = self.collect_work_items()
            self.analyze_work_patterns()

    def analyze(self) -> None:
        """Run analysis and display results."""
        count_word = plural(self.data_source.item_name, self.stats.total_items, show_num=False)
        console.print(f"[bold green]{self.stats.total_items:,} {count_word}:[/bold green]")

        # Display time span information
        if time_span := TimeSpan.from_stats(self.stats):
            for message in self.time_analyzer.format_time_span(
                time_span, self.data_source.item_name
            ):
                console.print(f" {message}")

        # Display session statistics
        session_stats = self.session_analyzer.calculate_session_stats(self.stats)
        console.print(
            f"\n[bold green]{session_stats.count:,} {plural('working session', session_stats.count, show_num=False)}:[/bold green]"
        )
        for message in self.session_analyzer.format_session_stats(
            session_stats, self.data_source.item_name
        ):
            console.print(f" {message}")

        # Display time distribution
        time_dist = self.time_analyzer.calculate_time_distribution(self.stats)

        console.print(f"\n[bold green]{count_word.capitalize()} by day of week:[/bold green]")
        for message in self.time_analyzer.format_distribution(
            time_dist, self.data_source.item_name
        ):
            console.print(f" {message}")

        console.print("\n[bold green]Most active hours:[/bold green]")
        for message in self.time_analyzer.format_most_active_hours(
            time_dist, self.data_source.item_name
        ):
            console.print(f" {message}")

        # Display streak information
        console.print("\n[bold green]Streaks:[/bold green]")
        streak_stats = self.streak_analyzer.calculate_streaks(self.stats)
        for message in self.streak_analyzer.format_streak_stats(streak_stats):
            console.print(f" {message}")

        # Display summary statistics and total work time
        console.print("\n[bold green]Totals:[/bold green]")
        summary_stats = self.summary_analyzer.calculate_summary_stats(self.stats)
        for message in self.summary_analyzer.format_summary_stats(
            summary_stats, self.data_source.item_name
        ):
            console.print(f" {message}")

        # Display total work time
        console.print("\n[bold green]Total work time:[/bold green]", end="")
        console.print(f" {self.summary_analyzer.format_total_work_time(summary_stats)}")

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


def parse_relative_date(date_str: str) -> datetime.date:
    """Parse relative date expressions like '30d', '1w', '1m'.

    Raises:
        ValueError: If the relative date can't be parsed.
    """
    today = datetime.datetime.now(tz=TZ).date()

    if not date_str.endswith(("d", "w", "m")):
        msg = f"Invalid relative date format: {date_str}. Use format like '30d', '1w', or '1m'"
        raise ValueError(msg)

    try:
        number = int(date_str[:-1])
        unit = date_str[-1]

        if unit == "d":
            return today - datetime.timedelta(days=number)
        if unit == "w":
            return today - datetime.timedelta(weeks=number)
        if unit == "m":
            # Approximate months as 30 days
            return today - datetime.timedelta(days=number * 30)
        msg = f"Invalid time unit: {unit}. Use 'd' (days), 'w' (weeks), or 'm' (months)"
        raise ValueError(msg)
    except ValueError as e:
        msg = f"Invalid relative date format: {date_str}. Use format like '30d', '1w', or '1m'"
        raise ValueError(msg) from e


def create_dynamic_parser() -> argparse.ArgumentParser:
    """Create argument parser with dynamic subparsers based on registered plugins.

    Raises:
        RuntimeError: If no data source plugins are registered.
    """
    # Get all available plugins
    all_plugins = list(PluginRegistry.get_all_plugins())

    if not all_plugins:
        msg = "No data source plugins are registered"
        raise RuntimeError(msg)

    # Create examples dynamically
    examples = []
    for plugin_class in all_plugins:
        examples.extend([
            f"  # {plugin_class.help_text} in the past 30 days",
            f"  workcalc {plugin_class.source_name} /path/to/source --since 30d",
            "",
            f"  # {plugin_class.help_text} for 2024",
            f"  workcalc {plugin_class.source_name} /path/to/source --start 01/01/2024 --end 12/31/2024",
            "",
            f"  # {plugin_class.help_text} with custom break time",
            f"  workcalc {plugin_class.source_name} /path/to/source --break-time 90 --min-work 20",
            "",
        ])

    parser = argparse.ArgumentParser(
        description="Calculate work patterns from various data sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
{chr(10).join(examples)}
        """,
    )

    subparsers = parser.add_subparsers(dest="source_type", required=True, help="Data source type")

    # Create subparsers dynamically based on registered plugins
    for plugin_class in all_plugins:
        subparser = subparsers.add_parser(
            plugin_class.source_name,
            help=plugin_class.help_text,
            description=plugin_class.description,
        )

        # Add plugin-specific arguments
        plugin_class.add_arguments(subparser)

        # Add common arguments
        subparser.add_argument(
            "-b",
            "--break-time",
            type=int,
            default=60,
            help="Minutes of inactivity to consider a session break (default: 60)",
        )
        subparser.add_argument(
            "-m",
            "--min-work",
            type=int,
            default=15,
            help="Minimum minutes to count per work item (default: 15)",
        )

        # Time range arguments
        time_group = subparser.add_mutually_exclusive_group()
        time_group.add_argument("--since", help="Start date: MM/DD/YYYY or relative (30d, 1w, 1m)")
        time_group.add_argument("--start", help="Start date in MM/DD/YYYY format")
        time_group.add_argument("--end", help="End date in MM/DD/YYYY format")

    return parser


def main() -> None:
    """Calculate work patterns from various data sources.

    Raises:
        ValueError: If the data source is invalid.
    """
    # Initialize plugins
    initialize_plugins()

    parser = create_dynamic_parser()
    args = parser.parse_args()

    # Parse date arguments
    start_date = None
    end_date = None

    if args.since:
        start_date = parse_relative_date(args.since)
    elif args.start:
        start_date = parse_date(args.start)

    if args.end:
        end_date = parse_date(args.end)

    config = WorkAnalysisConfig(
        break_time=args.break_time,
        min_work_per_item=args.min_work,
        start_date=start_date,
        end_date=end_date,
    )

    # Get plugin class and create data source instance
    plugin_class = PluginRegistry.get_plugin(args.source_type)
    if not plugin_class:
        msg = f"Unknown data source type: {args.source_type}"
        raise ValueError(msg)

    data_source = plugin_class.from_args(args)

    calculator = WorkCalculator(data_source, config)
    calculator.analyze()
