"""Sort files into folders based on filename suffix.

This script looks at filenames in the current folder to determine if they have a suffix, then allows
the user to select suffixes that should be sorted into subfolders created based on the suffix.
"""

from __future__ import annotations

import sys
from pathlib import Path

import inquirer
from polykit.cli import confirm_action, walking_man
from polykit.core import polykit_setup
from polykit.env import PolyEnv
from polykit.files import PolyFile
from polykit.formatters import color
from polykit.log import PolyLog

from dsbin.logic import Bounce, BounceParser

polykit_setup()

env = PolyEnv()
env.add_debug_var()
files = PolyFile()
logger = PolyLog.get_logger(level=env.log_level, simple=True)


def get_unique_suffixes(bounces: list[Bounce]) -> list[str]:
    """Get all unique suffixes from the bounce files."""
    suffixes = {bounce.suffix for bounce in bounces if bounce.suffix}
    return sorted(suffixes)


def prompt_user_for_suffixes(suffixes: list[str]) -> list[str]:
    """Prompt the user to select suffixes for folder creation."""
    questions = [
        inquirer.Checkbox(
            "selected_suffixes",
            message="Select suffixes to create folders for and sort files into",
            choices=suffixes,
            default=suffixes,
        )
    ]
    answers = inquirer.prompt(questions)

    if not answers:
        logger.error("No suffixes selected. Exiting the script.")
        sys.exit(1)

    return answers.get("selected_suffixes", [])


def sort_bounces(bounces: list[Bounce], selected_suffixes: list[str]) -> None:
    """Sort bounce files into folders based on selected suffixes."""
    duplicates: list[Path] = []

    for suffix in selected_suffixes:
        if matching_bounces := [bounce for bounce in bounces if bounce.suffix == suffix]:
            destination_folder = Path(suffix)

            # Check if folder exists before trying to create it
            if not destination_folder.exists():
                destination_folder.mkdir()
                logger.info("\nCreated folder: %s", suffix)
            else:
                logger.debug("\nUsing existing folder: %s", suffix)

            for bounce in matching_bounces:
                source = bounce.file_path
                destination = destination_folder / source.name

                if destination.exists():
                    logger.info(
                        "%s already exists in the %s folder.",
                        color(source.name, "cyan"),
                        color(suffix, "cyan"),
                    )
                    duplicates.append(source)
                    continue

                if files.move(source, destination, overwrite=False):
                    logger.info(
                        "%s -> %s",
                        color(source.name, "white"),
                        color(str(destination), "green"),
                    )
                else:
                    logger.warning("Failed to move %s to %s.", source.name, destination)

    if duplicates:
        handle_duplicates(duplicates)


def handle_duplicates(duplicates: list[Path]) -> None:
    """Handle duplicate files that are already sorted."""
    print("\nFound duplicate files that are already sorted:")
    for file in duplicates:
        print(color(f"✖ {file.name}", "yellow"))

    if confirm_action("\nDelete duplicate source files?", default_to_yes=False):
        successful, failed = files.delete(duplicates)
        if successful:
            print(
                color(
                    f"\n{successful} duplicate{'s' if len(successful) != 1 else ''} deleted.",
                    "green",
                )
            )
        if failed:
            print(color(f"{failed} deletion{'s' if len(failed) != 1 else ''} failed.", "red"))


def scan_bounces() -> tuple[list[Bounce], list[str]]:
    """Scan bounce files and determine common suffixes."""
    with walking_man("Scanning bounce files...", "cyan"):
        directory = Path.cwd()

        # Get all bounces
        all_bounces = BounceParser.find_bounces(directory)
        logger.debug("All bounces found: %s", len(all_bounces))

        # Get unique suffixes
        unique_suffixes = get_unique_suffixes(all_bounces)
        logger.debug("Unique suffixes found: %s", unique_suffixes)

        if not unique_suffixes:
            logger.debug("No suffixes found in bounce list.")
            return [], []

        # Filter the bounces
        suffixed_bounces = [bounce for bounce in all_bounces if bounce.suffix in unique_suffixes]

        return suffixed_bounces, unique_suffixes


def main() -> None:
    """Sort bounce files into folders based on automatically detected suffixes in their names."""
    bounces, common_suffixes = scan_bounces()

    if common_suffixes:
        if selected_suffixes := prompt_user_for_suffixes(common_suffixes):
            print("\nSorting bounce files...")
            sort_bounces(bounces, selected_suffixes)
            print(color("\nBounce files sorted successfully.", "green"))
        else:
            logger.info("No suffixes selected. Exiting the script.")
    else:
        logger.info("No common suffixes found. No bounce files require sorting.")
