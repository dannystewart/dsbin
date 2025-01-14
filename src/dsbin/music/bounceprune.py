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

This script will delete 1, 1a, and 1b, then rename 1c to 1, or with the --major flag, the script
will consolidate down to one bounce per day named by date with no suffix.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from dsutil import configure_traceback
from dsutil.files import delete_files
from dsutil.shell import confirm_action
from dsutil.text import color, print_colored

from dsbin.music.bounce_parser import Bounce, BounceParser

if TYPE_CHECKING:
    from datetime import datetime

configure_traceback()


def determine_actions(
    bounce_groups: dict[tuple, dict[str, list[Bounce]]], major_only: bool = False
) -> dict:
    """Given a dictionary of bounce groups, determine the actions to be taken on the bounces.

    Args:
        bounce_groups: A dictionary of bounce groups where the keys are tuples representing the
                       bounce attributes and the values are lists of Bounce objects.
        major_only: If True, consolidate to one bounce per day, renumbering to version 0.

    Returns:
        A dictionary containing the actions to be performed on the files.
    """
    actions = {"trash": [], "rename": []}

    # Group bounces by title and date
    by_date: dict[tuple[str, datetime], list[Bounce]] = {}
    for (title, date, _), suffix_groups in bounce_groups.items():
        key = (title, date)
        if key not in by_date:
            by_date[key] = []
        for bounces in suffix_groups.values():
            by_date[key].extend(bounces)

    if major_only:
        handle_major(by_date, actions)
    else:
        handle_minor(by_date, actions)

    return actions


def handle_major(by_date: dict[tuple[str, datetime], list[Bounce]], actions: dict) -> None:
    """Keep only one bounce per day (_0, _1, etc. renamed to _0)."""
    for bounces in by_date.values():
        if len(bounces) <= 1:
            continue

        sorted_bounces = BounceParser.sort_bounces(bounces)
        latest = sorted_bounces[-1]

        # Trash all but the latest
        actions["trash"].extend(b.file_path for b in sorted_bounces[:-1])

        # Rename the latest to version 0
        new_name = latest.file_path.with_stem(
            f"{latest.title} {latest.date.strftime('%y.%-m.%-d')}"
        )
        if latest.suffix:
            new_name = new_name.with_stem(f"{new_name.stem} {latest.suffix}")

        if latest.version != 0 or latest.minor_version:
            actions["rename"].append((latest.file_path, new_name))


def handle_minor(by_date: dict[tuple[str, datetime], list[Bounce]], actions: dict) -> None:
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
                actions["trash"].extend(b.file_path for b in same_version[:-1])

                # Rename the latest minor version to just the major version
                if latest.minor_version:
                    new_name = latest.file_path.with_stem(
                        f"{latest.title} {latest.date.strftime('%y.%-m.%-d')}_{latest.version}"
                    )
                    if latest.suffix:
                        new_name = new_name.with_stem(f"{new_name.stem} {latest.suffix}")
                    actions["rename"].append((latest.file_path, new_name))


def print_actions(actions: dict[str, list]) -> None:
    """Print the actions to be performed on files.

    Args:
        actions: A dictionary containing the actions to be performed on the files.
    """
    if not actions["trash"] and not actions["rename"]:
        print_colored("No actions to perform.", "green")
        return

    if actions["trash"]:
        print_colored("Files to Trash:", "red")
        sorted_trash = sorted(actions["trash"], key=lambda x: BounceParser.get_bounce(x).date)
        for file in sorted_trash:
            print_colored(f"✖ {file.name}", "red")
    else:
        print_colored("No files to trash.", "green")

    if actions["rename"]:
        print_colored("\nFiles to Rename:", "yellow")
        sorted_rename = sorted(actions["rename"], key=lambda x: BounceParser.get_bounce(x[0]).date)
        for old_path, new_path in sorted_rename:
            print(old_path.name + color(" → ", "yellow") + color(new_path.name, "green"))
    else:
        print_colored("No files to rename.", "green")

    print()


def execute_actions(actions: dict[str, list]) -> None:
    """Execute a series of actions on a given directory."""
    if confirm_action("Proceed with these actions?", default_to_yes=False):
        successful_deletions, failed_deletions = delete_files(actions["trash"], show_output=False)

        renamed_files_count = 0
        for old_path, new_path in actions["rename"]:
            old_path.rename(new_path)
            renamed_files_count += 1

        completion_message_parts = []
        if successful_deletions > 0:
            completion_message_parts.append(
                f"{successful_deletions} file{'s' if successful_deletions > 1 else ''} deleted"
            )
        if failed_deletions > 0:
            completion_message_parts.append(
                f"{failed_deletions} deletion{'s' if failed_deletions > 1 else ''} failed"
            )
        if renamed_files_count > 0:
            completion_message_parts.append(
                f"{renamed_files_count} file{'s' if renamed_files_count > 1 else ''} renamed"
            )

        completion_message = ", ".join(completion_message_parts) + "."
        print_colored(completion_message, "green")
    else:
        print_colored("Actions cancelled.", "red")


def main() -> None:
    """Process audio files in the current working directory by finding the bounces, grouping them,
    determining and printing the actions to be taken, and then executing them.
    """
    parser = argparse.ArgumentParser(description="Prune and consolidate Logic bounce files.")
    parser.add_argument(
        "--major",
        action="store_true",
        help="Consolidate to one bounce per day, renumbering to version 0",
    )
    args = parser.parse_args()

    directory = Path.cwd()
    bounces = BounceParser.find_bounces(directory)
    bounce_groups = BounceParser.group_bounces(bounces)
    actions = determine_actions(bounce_groups, major_only=args.major)
    print_actions(actions)
    execute_actions(actions)


if __name__ == "__main__":
    main()
