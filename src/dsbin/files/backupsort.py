#!/usr/bin/env python3

"""
Sorts saved backup files by adding a timestamp suffix to the filename.

This script is designed to sort backup files by adding a timestamp suffix to the filename.
This was originally created for dealing with a large number of SQL dumps and backups being
downloaded with the same filename, but it can be used for any type of file.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import time

from natsort import natsorted

from dsutil import configure_traceback
from dsutil.shell import confirm_action
from dsutil.text import color

configure_traceback()

BACKUP_PATH = "/Users/danny/Library/CloudStorage/OneDrive-Personal/Documents/Archive/Backups/Bots"


def is_already_renamed(filename: str) -> int:
    """Check if the file already contains a timestamp matching the suffix format."""
    timestamp_patterns = re.findall(r"_\d{6}_\d{4}", filename)
    return len(timestamp_patterns)


def format_timestamp(file_path: str) -> str:
    """Get the last modification time of a file and format it as a string."""
    mtime = os.path.getmtime(file_path)
    return time.strftime("%y%m%d_%H%M", time.localtime(mtime))


def clean_filename(filename: str, timestamp_count: int) -> str:
    """
    Clean a filename by removing unwanted patterns including ".dump", " copy", "(1)", dates in
    "_YYYY-MM-DD" format, and extra spaces.

    Args:
        filename: The filename to clean.
        timestamp_count: The number of timestamp suffixes found.

    Returns:
        The cleaned filename.
    """
    clean_basename = re.sub(r"\.dump", "", filename)
    clean_basename = re.sub(r"\s*\bcopy\b\s*\d*|\(\d+\)|_\d{4}-\d{2}-\d{2}", "", clean_basename)

    if timestamp_count > 1:
        clean_basename = re.sub(r"_\d{6}_\d{4}(?=_\d{6}_\d{4})", "", clean_basename)

    return re.sub(r"\s+\.", ".", clean_basename).strip()


def get_files_to_process(args: argparse.Namespace) -> list:
    """Get the list of files to process based on command line arguments."""
    files_to_process = args.files if args.files else os.listdir(".")
    expanded_files = []
    for file_pattern in files_to_process:
        expanded_files.extend(glob.glob(file_pattern))
    return natsorted(expanded_files)


def process_file(filename: str) -> tuple | None:
    """Process a single file and return planned changes if any."""
    if filename.startswith(".") or not os.path.isfile(filename):
        return None

    timestamp_count = is_already_renamed(filename)

    if timestamp_count == 0:
        formatted_timestamp = format_timestamp(filename)
        clean_name = clean_filename(filename, timestamp_count)
        base_name, extension = os.path.splitext(clean_name)
        new_name = f"{base_name}_{formatted_timestamp}{extension}"
        print(color(filename, "blue") + " ➔ " + color(new_name, "green"))
        return filename, new_name

    if timestamp_count >= 1:
        if timestamp_count == 1:
            print(color(filename, "yellow") + " has already been renamed, skipping.")
            return None

        print(color(filename, "red") + " was renamed multiple times, trimming extra timestamps.")
        clean_name = clean_filename(filename, timestamp_count)
        base_name, extension = os.path.splitext(clean_name)
        new_name = f"{base_name}{extension}"
        print(color(filename, "blue") + " ➔ " + color(new_name, "green"))
        return filename, new_name


def perform_operations(planned_changes: list, args: argparse.Namespace) -> None:
    """Execute the planned changes if confirmed by the user."""
    if planned_changes and confirm_action("Proceed with renaming?"):
        for old_name, new_name in planned_changes:
            final_path = new_name
            action_str = "Renamed"
            if not args.rename_only:
                final_path = os.path.join(BACKUP_PATH, new_name)
                action_str = "Renamed and moved"
            os.rename(old_name, final_path)
            print(color(f"{action_str} {old_name}", "blue") + " ➔ " + color(final_path, "green"))
    elif planned_changes:
        print("Renaming canceled.")
    else:
        print("No files to rename.")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sorts and moves backup files to a designated directory.",
    )
    parser.add_argument(
        "--rename-only",
        action="store_true",
        help="Only rename files, do not move them to the backup directory.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        default=[],
        help="Specific files or wildcards to process. If not provided, all files in the current directory will be processed.",
    )
    return parser.parse_args()


def main() -> None:
    """Rename and move files based on the command-line arguments."""
    args = parse_arguments()
    files_to_process = get_files_to_process(args)
    planned_changes = []

    for filename in files_to_process:
        if result := process_file(filename):
            planned_changes.append(result)

    perform_operations(planned_changes, args)


if __name__ == "__main__":
    main()
