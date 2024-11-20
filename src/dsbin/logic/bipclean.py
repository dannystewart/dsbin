"""
Identifies and deletes AIFF files created within a specified time period (default 24 hours).

This script is for audio files bounced in place within a Logic project. These files end up in the
Audio Files folder, but if you decide to revert or save the project without keeping it, they're not
deleted. This script identifies and deletes these files without the need for a full project cleanup.

By default, this looks for files created within the last 4 hours. You can override this with any
value by using the `--hours` argument. Files are listed and confirmed before deletion.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dsutil.files import delete_files, list_files
from dsutil.shell import confirm_action
from dsutil.text import print_colored

DEFAULT_HOURS = 4


def parse_args() -> argparse.Namespace:
    """Parse arguments passed in from the command line."""
    parser = argparse.ArgumentParser(description="find and delete recent AIFF files")
    parser.add_argument(
        "--hours", type=int, default=DEFAULT_HOURS, help="hours to look back (default: 4)"
    )
    return parser.parse_args()


def main() -> None:
    """Find and delete AIFF files created within the specified time period."""
    args = parse_args()
    current_dir = os.getcwd()
    time_duration = datetime.now(tz=ZoneInfo("America/New_York")) - timedelta(hours=args.hours)

    # List AIFF files created within the specified time period
    aif_files = list_files(directory=current_dir, extensions=["aif"], modified_after=time_duration)

    if not aif_files:  # If no files are found, exit
        print_colored(f"No AIFF files from within the last {args.hours} hours.", "green")
        if args.hours == DEFAULT_HOURS:
            print_colored("You can use --hours to specify a different time period.", "cyan")
        return

    print_colored(f"The following AIFF files were created in the last {args.hours} hours:", "green")
    for file in aif_files:
        print(f"- {file}")

    if confirm_action("Delete the files?", default_to_yes=True):
        delete_files(aif_files)
    else:
        print("No files were deleted.")


if __name__ == "__main__":
    main()
