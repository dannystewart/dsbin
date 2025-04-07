"""Prunes and consolidates bounces from Logic projects.

This script is designed to prune and consolidate bounces from Logic projects. I have a
specific naming scheme that I use to keep track of different versions. Part of that is for
"draft" versions that don't need to be kept for long. This script helps me keep my bounce
folders cleaner (and save disk space) by deleting old bounces that I don't need anymore
and making sure the naming is consistent.

My naming scheme is primarily based on date with an incrementing version number:
Project Name 23.11.20_0.wav
Project Name 23.11.20_1.wav
Project Name 23.11.20_2.wav

Incremental draft versions with very quick and minor tweaks/fixes follow this format:
Project Name 23.11.20_1.wav
Project Name 23.11.20_1a.wav
Project Name 23.11.20_1b.wav
Project Name 23.11.20_1c.wav

This script will delete 1, 1a, and 1b, then rename 1c to 1, or with the `-d` / `--daily` flag, the
script will consolidate down to one bounce per day named by date with no suffix. The `-s` or
`--skip-latest` flag can be used to skip the most recent day's bounces if work is still in progress.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import confirm_action, walking_man
from polykit.core import polykit_setup
from polykit.files import PolyFile
from polykit.formatters import color, print_color

from dsbin.logic.bounce_parser import Bounce, BounceParser

if TYPE_CHECKING:
    from datetime import datetime

polykit_setup()


@dataclass
class BounceActions:
    """Dataclass to hold the actions to be taken on bounces."""

    trash: list[Path]
    rename: list[tuple[Path, Path]]


def determine_actions(
    bounce_groups: dict[tuple[str, datetime, int], dict[str, list[Bounce]]],
    daily: bool = False,
    skip_latest: bool = False,
) -> BounceActions:
    """Given a dictionary of bounce groups, determine the actions to be taken on the bounces.

    Args:
        bounce_groups: A dictionary of bounce groups where the keys are tuples representing the
                       bounce attributes and the values are lists of Bounce objects.
        daily: If True, keep only the last bounce for each day and remove the version number.
        skip_latest: If True, don't take any action on the most recent day's bounces.

    Returns:
        A BounceActions object containing the actions to be performed on the files.
    """
    actions = BounceActions(trash=[], rename=[])

    # Group bounces by title and date
    by_date: dict[tuple[str, datetime], list[Bounce]] = {}
    for (title, date, _), suffix_groups in bounce_groups.items():
        key = (title, date)
        if key not in by_date:
            by_date[key] = []
        for bounces in suffix_groups.values():
            by_date[key].extend(bounces)

    # If skip_latest is True, identify and remove the most recent date for each title
    if skip_latest and by_date:
        # Extract titles and find the latest date for each
        titles = {key[0] for key in by_date}
        latest_dates_by_title = {}

        for title in titles:
            title_dates = [date for t, date in by_date if t == title]
            if title_dates:
                latest_dates_by_title[title] = max(title_dates)

        # Filter out the latest date for each title
        by_date = {
            key: bounces
            for key, bounces in by_date.items()
            if key[1] != latest_dates_by_title.get(key[0])
        }

    if daily:
        handle_major(by_date, actions)
    else:
        handle_minor(by_date, actions)

    return actions


def handle_major(by_date: dict[tuple[str, datetime], list[Bounce]], actions: BounceActions) -> None:
    """Keep only one bounce per day per suffix, removing version numbers entirely."""
    # Regroup bounces by title, date, and suffix
    by_date_and_suffix: dict[tuple[str, datetime, str | None], list[Bounce]] = {}
    for bounces in by_date.values():
        for bounce in bounces:
            key = (bounce.title, bounce.date, bounce.suffix)
            if key not in by_date_and_suffix:
                by_date_and_suffix[key] = []
            by_date_and_suffix[key].append(bounce)

    for bounces in by_date_and_suffix.values():
        sorted_bounces = BounceParser.sort_bounces(bounces)
        latest = sorted_bounces[-1]

        # For multiple bounces, trash all but the latest of this suffix variant
        if len(bounces) > 1:
            actions.trash.extend(b.file_path for b in sorted_bounces[:-1])

        # Always check if the file needs renaming to remove version
        current_stem = latest.file_path.stem
        new_stem = f"{latest.title} {latest.date.strftime('%y.%-m.%-d')}"
        if latest.suffix:
            new_stem = f"{new_stem} {latest.suffix}"

        if current_stem != new_stem:
            new_name = latest.file_path.with_stem(new_stem)
            actions.rename.append((latest.file_path, new_name))


def handle_minor(by_date: dict[tuple[str, datetime], list[Bounce]], actions: BounceActions) -> None:
    """Keep only one bounce per version (_1a, _1b, etc. renamed to _1)."""
    for bounces in by_date.values():
        if len(bounces) <= 1:
            continue

        sorted_bounces = BounceParser.sort_bounces(bounces)
        latest = sorted_bounces[-1]

        # If we have minor versions, clean those up
        if any(b.minor_version for b in sorted_bounces):
            same_version = [b for b in sorted_bounces if b.version == latest.version]
            if len(same_version) > 1:
                # Trash all but the latest minor version
                actions.trash.extend(b.file_path for b in same_version[:-1])

                # Rename the latest minor version to just the major version
                if latest.minor_version:
                    new_name = latest.file_path.with_stem(
                        f"{latest.title} {latest.date.strftime('%y.%-m.%-d')}_{latest.version}"
                    )
                    if latest.suffix:
                        new_name = new_name.with_stem(f"{new_name.stem} {latest.suffix}")
                    actions.rename.append((latest.file_path, new_name))


def prepare_output(actions: BounceActions) -> tuple[list[str], list[str]]:
    """Prepare the sorted lists of files for output.

    Args:
        actions: A BounceActions object containing the actions to be performed on the files.

    Returns:
        A tuple of (trash_files, rename_files) where each is a list of formatted strings.
    """
    if not actions.trash and not actions.rename:
        return [], []

    # Sort and prepare trash files
    trash_files = []
    if actions.trash:
        sorted_trash = sorted(actions.trash, key=lambda x: BounceParser.get_bounce(x).date)
        trash_files = [f"✖ {file.name}" for file in sorted_trash]

    # Sort and prepare rename files
    rename_files = []
    if actions.rename:
        sorted_rename = sorted(actions.rename, key=lambda x: BounceParser.get_bounce(x[0]).date)
        rename_files = [
            f"{old_path.name} → {new_path.name}" for old_path, new_path in sorted_rename
        ]

    return trash_files, rename_files


def execute_actions(actions: BounceActions) -> None:
    """Execute a series of actions on a given directory."""
    if not actions.trash and not actions.rename:
        return

    if confirm_action("Proceed with these actions?", default_to_yes=False):
        files = PolyFile()
        successful_deletions, failed_deletions = files.delete(actions.trash)

        renamed_files_count = 0
        for old_path, new_path in actions.rename:
            old_path.rename(new_path)
            renamed_files_count += 1

        completion_message_parts = []
        if len(successful_deletions) > 0:
            completion_message_parts.append(
                f"{successful_deletions} file{'s' if len(successful_deletions) > 1 else ''} deleted"
            )
        if len(failed_deletions) > 0:
            completion_message_parts.append(
                f"{failed_deletions} deletion{'s' if len(failed_deletions) > 1 else ''} failed"
            )
        if renamed_files_count > 0:
            completion_message_parts.append(
                f"{renamed_files_count} file{'s' if renamed_files_count > 1 else ''} renamed"
            )

        completion_message = ", ".join(completion_message_parts) + "."
        print_color(completion_message, "green")
    else:
        print_color("Actions canceled.", "red")


def print_actions(trash_files: list[str], rename_files: list[str]) -> None:
    """Print the actions to be performed on files."""
    if not trash_files and not rename_files:
        print_color("No actions to perform.", "green")
        return

    if trash_files:
        print_color("Files to Trash:", "red")
        for line in trash_files:
            print_color(line, "red")
    else:
        print_color("No files to trash.", "green")

    if rename_files:
        print_color("\nFiles to Rename:", "yellow")
        for line in rename_files:
            old_name, new_name = line.split(" → ")
            print(old_name + color(" → ", "yellow") + color(new_name, "green"))
    else:
        print_color("No files to rename.", "green")

    print()


def main() -> None:
    """Process audio files in the current working directory."""
    parser = argparse.ArgumentParser(description="Prune and consolidate Logic bounce files.")
    parser.add_argument(
        "-d", "--daily", action="store_true", help="keep only the last bounce for each day"
    )
    parser.add_argument(
        "-s", "--skip-latest", action="store_true", help="skip the most recent day's bounces"
    )
    args = parser.parse_args()

    directory = Path.cwd()

    with walking_man("Analyzing bounce files...", "cyan"):
        bounces = BounceParser.find_bounces(directory)
        bounce_groups = BounceParser.group_bounces(bounces)
        actions = determine_actions(bounce_groups, daily=args.daily, skip_latest=args.skip_latest)
        trash_files, rename_files = prepare_output(actions)

    print_actions(trash_files, rename_files)
    execute_actions(actions)


if __name__ == "__main__":
    main()
