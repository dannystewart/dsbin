"""Sort files into folders based on filename suffix.

This script looks at filenames in the current folder to determine if they have a suffix, then allows
the user to select suffixes that should be sorted into subfolders created based on the suffix.
"""

from __future__ import annotations

import sys
from pathlib import Path

import inquirer

from dsutil import LocalLogger, configure_traceback
from dsutil.animation import walking_animation
from dsutil.env import DSEnv
from dsutil.files import move_file
from dsutil.progress import halo_progress
from dsutil.text import color

from dsbin.music.bounce_parser import Bounce, BounceParser

configure_traceback()

env = DSEnv()
env.add_debug_var()

log_level = "debug" if env.debug else "info"
logger = LocalLogger().get_logger(level=log_level, simple=True)


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
    for suffix in selected_suffixes:
        if matching_bounces := [bounce for bounce in bounces if bounce.suffix == suffix]:
            destination_folder = Path(suffix)
            destination_folder.mkdir(exist_ok=True)
            logger.info("\nCreated folder: %s", suffix)

            for bounce in matching_bounces:
                source = bounce.file_path
                destination = destination_folder / source.name

                if destination.exists():
                    logger.info(
                        "%s already exists in the %s folder.",
                        color(source.name, "cyan"),
                        color(suffix, "cyan"),
                    )
                    continue

                if move_file(source, destination, overwrite=False, show_output=False):
                    logger.info(
                        "%s -> %s",
                        color(source.name, "green"),
                        color(destination, "green"),
                    )
                else:
                    logger.warning("Failed to move %s to %s.", source.name, destination)


def scan_bounces() -> tuple[list[Bounce], list[str]]:
    """Scan bounce files and determine common suffixes."""
    with walking_animation("Scanning bounce files...", "cyan"):
        directory = Path.cwd()

        all_bounces = BounceParser.find_bounces(directory)
        logger.debug("All bounces found: %s", len(all_bounces))

        unique_suffixes = get_unique_suffixes(all_bounces)
        logger.debug("Unique suffixes found: %s", unique_suffixes)

        if not unique_suffixes:
            logger.debug("No suffixes found in bounce list.")
            return [], []

        suffixed_bounces = []
        for suffix in unique_suffixes:
            filtered = BounceParser.filter_by_suffix(directory, suffix)
            suffixed_bounces.extend(filtered)

        return suffixed_bounces, unique_suffixes


def main() -> None:
    """Sort bounce files into folders based on automatically detected suffixes in their names."""
    bounces, common_suffixes = scan_bounces()

    if common_suffixes:
        if selected_suffixes := prompt_user_for_suffixes(common_suffixes):
            with halo_progress(
                start_message="Sorting bounce files", end_message="Bounce files sorted successfully"
            ):
                sort_bounces(bounces, selected_suffixes)
        else:
            logger.info("No suffixes selected. Exiting the script.")
    else:
        logger.info("No common suffixes found. No bounce files require sorting.")
