#!/usr/bin/env python3

"""CLI tool for working with Logic bounce files using BounceParser."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import ArgParser
from polykit.formatters import color

from dsbin.logic.bounce_parser import Bounce, BounceParser

if TYPE_CHECKING:
    import argparse


def print_bounce(bounce: Bounce) -> None:
    """Print a bounce with color-coded components for easier visual parsing."""
    title = color(bounce.title, "blue")
    date = color(bounce.date.strftime("%y."), "blue")
    date += color(bounce.date.strftime("%-m.%-d"), "green", style=["bold"])
    version = color(f"_{bounce.full_version}", "green")
    suffix = color(f" {bounce.suffix}", "green") if bounce.suffix else ""
    ext = color(f".{bounce.file_format}", "blue")

    print(f"{title} {date}{version}{suffix}{ext}")


def list_bounces(args: argparse.Namespace) -> None:
    """List bounces, optionally filtered by various criteria."""
    bounces = BounceParser.find_bounces(args.dir)

    if args.suffix:
        bounces = [b for b in bounces if b.suffix == args.suffix]
    if args.format:
        bounces = [b for b in bounces if b.file_format.lower() == args.format.lower()]
    if args.title:
        bounces = [b for b in bounces if args.title.lower() in b.title.lower()]

    sorted_bounces = BounceParser.sort_bounces(bounces)

    for bounce in sorted_bounces:
        print_bounce(bounce)


def latest(args: argparse.Namespace) -> None:
    """Show the latest bounce(s)."""
    include_suffixed = args.include_suffixed

    if args.per_day:
        latest_bounces = BounceParser.get_latest_per_day(args.directory, include_suffixed)
        for bounce in latest_bounces:
            print_bounce(bounce)
    else:
        bounces = BounceParser.find_bounces(args.directory)
        latest_bounce = BounceParser.get_latest_bounce(bounces, include_suffixed)
        print_bounce(latest_bounce)


def get_parser() -> argparse.ArgumentParser:
    """Parse command-line arguments."""
    parser = ArgParser(description="Work with Logic bounce files")
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="directory to search (default: current directory)",
    )

    subparsers = parser.add_subparsers(dest="command", help="command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="list bounces")
    list_parser.add_argument("--suffix", help="filter by suffix")
    list_parser.add_argument("--format", help="filter by file format")
    list_parser.add_argument("--title", help="filter by title (substring match)")
    list_parser.set_defaults(func=list_bounces)

    # Latest command
    latest_parser = subparsers.add_parser("latest", help="show latest bounce(s)")
    latest_parser.add_argument(
        "--per-day", action="store_true", help="show latest bounce for each day"
    )
    latest_parser.add_argument(
        "--include-suffixed",
        action="store_true",
        help="include suffixed bounces when determining latest",
    )
    latest_parser.set_defaults(func=latest)

    return parser


def main() -> None:
    """Parse arguments and execute the appropriate command."""
    parser = get_parser()
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
