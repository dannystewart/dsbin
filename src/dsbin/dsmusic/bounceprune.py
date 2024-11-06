"""
Prunes and consolidates bounces from Logic projects.

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

This script will delete 1, 1a, and 1b, then rename 1c to 1.
"""

from __future__ import annotations

from pathlib import Path

from .bounce_parser import Bounce, BounceParser

from dsutil.files import delete_files
from dsutil.shell import confirm_action
from dsutil.text import color, print_colored


def determine_actions(bounce_groups: dict[tuple, dict[str, list[Bounce]]]) -> dict:
    """
    Given a dictionary of bounce groups, determine the actions to be taken on the bounces.

    Args:
        bounce_groups: A dictionary of bounce groups where the keys are tuples representing the
            bounce attributes and the values are lists of Bounce objects.

    Returns:
        A dictionary containing the actions to be performed on the files.
    """
    actions = {"trash": [], "rename": []}

    for group in bounce_groups.values():
        for suffix_group in group.values():
            sorted_group = BounceParser.sort_bounces(suffix_group)
            if len(sorted_group) > 1:
                bounce = BounceParser.get_latest_bounce(sorted_group)
                actions["trash"].extend(b.file_path for b in sorted_group[:-1])

                if bounce.minor_version:
                    new_name = bounce.file_path.with_stem(
                        f"{bounce.title} {bounce.date.strftime('%y.%-m.%-d')}_{bounce.version}"
                    )
                    if bounce.suffix:
                        new_name = new_name.with_stem(f"{new_name.stem} {bounce.suffix}")

                    actions["rename"].append((bounce.file_path, new_name))

    return actions


def print_actions(actions: dict) -> None:
    """
    Print the actions to be performed on files.

    Args:
        actions: A dictionary containing the actions to be performed on the files.
    """
    if not actions["trash"] and not actions["rename"]:
        print_colored("No actions to perform.", "green")
        return

    if actions["trash"]:
        print_colored("Files to Trash:", "red")
        for file in sorted(actions["trash"], key=lambda x: x.name):
            print_colored(f"✖ {file.name}", "red")
    else:
        print_colored("No files to trash.", "green")

    if actions["rename"]:
        print_colored("\nFiles to Rename:", "yellow")
        for old_path, new_path in sorted(actions["rename"], key=lambda x: x[0].name):
            print(old_path.name + color(" → ", "yellow") + color(new_path.name, "green"))
    else:
        print_colored("No files to rename.", "green")

    print()  # Blank line at the end


def execute_actions(actions: dict) -> None:
    """
    Execute a series of actions on a given directory.

    Args:
        directory: The directory to execute the actions on.
        actions: A dictionary containing the actions to be performed on the files.
    """
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


def main(args_list: list[str] | None = None) -> None:  # noqa: ARG001
    """
    Process audio files in the current working directory by finding the bounces, grouping them,
    determining and printing the actions to be taken, and then executing them.
    """
    directory = Path.cwd()
    bounces = BounceParser.find_bounces(directory)
    bounce_groups = BounceParser.group_bounces(bounces)
    actions = determine_actions(bounce_groups)

    print_actions(actions)
    execute_actions(actions)


if __name__ == "__main__":
    main()
