"""Identifies and deletes AIFF files created within a specified time period (default 2 hours).

This script is for audio files bounced in place within a Logic project. These files end up in the
Audio Files folder, but if you decide to revert or save the project without keeping it, they're not
deleted. This script identifies and deletes these files without the need for a full project cleanup.

By default, this looks for files created within the last 2 hours. You can override this with any
value by using the --hours argument. Files can be individually selected for deletion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import inquirer

from dsbase import TZ, configure_traceback
from dsbase.files import FileManager
from dsbase.text import print_colored

configure_traceback()

DEFAULT_HOURS = 2

files = FileManager()


def parse_args() -> argparse.Namespace:
    """Parse arguments passed in from the command line."""
    parser = argparse.ArgumentParser(description="find and delete recent AIFF files")
    parser.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_HOURS,
        help=f"hours to look back (default: {DEFAULT_HOURS})",
    )
    return parser.parse_args()


def select_files(files: list[Path]) -> list[Path]:
    """Present a checkbox selection of files and return those selected."""
    if not files:
        return []

    choices = [
        inquirer.Checkbox(
            "files",
            message="Select files to delete",
            choices=[(str(f), f) for f in files],
            default=files,
        )
    ]

    answers = inquirer.prompt(choices)
    return answers["files"] if answers else []


def main() -> None:
    """Find and delete AIFF files created within the specified time period."""
    args = parse_args()
    hours = args.hours
    current_dir = Path.cwd()
    duration = datetime.now(tz=TZ) - timedelta(hours=hours)

    # Get all AIFF files and filter by recency
    aiff_files = files.list(dir=current_dir, exts=["aif"])
    recent_files = [
        f for f in aiff_files if datetime.fromtimestamp(f.stat().st_mtime, tz=TZ) > duration
    ]

    s = "s" if hours != 1 else ""
    if not recent_files:
        print_colored(f"No AIFF files from within the last {hours} hour{s}.", "green")
        if hours == DEFAULT_HOURS:
            print_colored("Use --hours to specify a different time period.", "cyan")
        return

    print_colored(f"Found {len(aiff_files)} AIFF files from the last {hours} hour{s}:", "green")
    selected_files = select_files(aiff_files)

    if not selected_files:
        print_colored("No files selected for deletion.", "yellow")
        return

    print_colored("\nThe following files will be deleted:", "yellow")
    for file in selected_files:
        print(f"- {file}")

    if len(selected_files) < len(aiff_files):
        skipped = len(aiff_files) - len(selected_files)
        print_colored(f"\n{skipped} file{'s' if skipped != 1 else ''} will be kept.", "cyan")

    files.delete(selected_files)
    print_colored("\nSelected files have been deleted.", "green")


if __name__ == "__main__":
    main()
