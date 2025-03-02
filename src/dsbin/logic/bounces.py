#!/usr/bin/env python3

"""CLI tool for working with Logic bounce files using BounceParser."""

from __future__ import annotations

import argparse
from pathlib import Path

from dsbin.logic.bounce_parser import BounceParser


def list_bounces(args: argparse.Namespace) -> None:
    """List bounces, optionally filtered by various criteria."""
    bounces = BounceParser.find_bounces(args.directory)

    if args.suffix:
        bounces = [b for b in bounces if b.suffix == args.suffix]
    if args.format:
        bounces = [b for b in bounces if b.file_format.lower() == args.format.lower()]
    if args.title:
        bounces = [b for b in bounces if args.title.lower() in b.title.lower()]

    sorted_bounces = BounceParser.sort_bounces(bounces)

    for bounce in sorted_bounces:
        suffix_str = f" {bounce.suffix}" if bounce.suffix else ""
        print(
            f"{bounce.title} {bounce.date.strftime('%y.%m.%d')}_{bounce.full_version}{suffix_str}.{bounce.file_format}"
        )


def latest(args: argparse.Namespace) -> None:
    """Show the latest bounce(s)."""
    bounces = BounceParser.find_bounces(args.directory)

    if args.per_day:
        latest_bounces = BounceParser.get_latest_per_day(args.directory)
        for bounce in latest_bounces:
            suffix_str = f" {bounce.suffix}" if bounce.suffix else ""
            print(
                f"{bounce.title} {bounce.date.strftime('%y.%m.%d')}_{bounce.full_version}{suffix_str}.{bounce.file_format}"
            )
    else:
        latest_bounce = BounceParser.get_latest_bounce(bounces)
        suffix_str = f" {latest_bounce.suffix}" if latest_bounce.suffix else ""
        print(
            f"{latest_bounce.title} {latest_bounce.date.strftime('%y.%m.%d')}_{latest_bounce.full_version}{suffix_str}.{latest_bounce.file_format}"
        )


def main():
    """Parse arguments and execute the appropriate command."""
    parser = argparse.ArgumentParser(description="Work with Logic bounce files")
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        default=Path.cwd(),
        help="directory to search (default: current directory)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List bounces")
    list_parser.add_argument("--suffix", help="Filter by suffix")
    list_parser.add_argument("--format", help="Filter by file format")
    list_parser.add_argument("--title", help="Filter by title (substring match)")
    list_parser.set_defaults(func=list_bounces)

    # Latest command
    latest_parser = subparsers.add_parser("latest", help="Show latest bounce(s)")
    latest_parser.add_argument(
        "--per-day", action="store_true", help="Show latest bounce for each day"
    )
    latest_parser.set_defaults(func=latest)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
