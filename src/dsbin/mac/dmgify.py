#!/usr/bin/env python3

"""Creates DMG files from folders, with specific handling for Logic projects.

This script automates the creation of DMG (Apple Disk Image) files from directories for archival and
backup. It has additional functionality to handle Logic Pro project folders with appropriate
exclusions and compression options to optimize the disk images for storage.

Features:

- Processes individual directories or batch processes all directories within a specified path.
- Handles directories as Logic Pro projects with the `--logic` flag, excluding non-essential subfolders.
- Offers LZMA compression with the `--lzma` flag for smaller but slower-to-create DMGs.
- Allows datestamping of DMG filenames with the `--date` flag, useful for versioning.
- Supports the `--backup` flag, combining LZMA compression and date appending in one option.
- Excludes specified directories from DMG creation with the `--exclude` flag, taking a comma-separated list.
- Overwrites existing DMG files if the `--force` option is specified, otherwise skips existing files.
- Performs a dry run with the `--dry-run` flag, which will output expected filenames without generating them.

The script ensures a clean state by creating a temporary folder to store interim files
during the creation process and performs cleanup of these resources on completion or failure.

Usage:

To create DMGs for all folders in the current directory, just run the script without any arguments.
Specify a folder by providing its path to process only that directory. Use the provided flags
(`--logic`, `--lzma`, `--date`, `--backup`, `--exclude`, and `--force`) to control the script's
behavior, or use `--help` to view all available options.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from dsutil import configure_traceback
from dsutil.files import delete_files, list_files, move_file
from dsutil.progress import halo_progress, with_retries
from dsutil.text import print_colored

if TYPE_CHECKING:
    import types

configure_traceback()

tz = ZoneInfo("America/New_York")

LOGIC_EXCLUSIONS = ["Bounces", "Old Bounces", "Movie Files", "Stems"]

resources_for_cleanup: dict[str, str | None] = {
    "temp_dmg": None,
    "current_sparsebundle": None,
}


def signal_handler(signum: int | None = None, frame: types.FrameType | None = None) -> None:  # noqa: ARG001
    """Handle signals and cleanup resources."""
    cleanup_resources()
    print_colored("Cleanup completed. Program interrupted.", "red")
    sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def should_exclude(folder_name: str, exclude_list: list[str]) -> bool:
    """Check if a folder should be excluded."""
    return folder_name in exclude_list


def rsync_folder(
    source: str, destination: str, exclude_patterns: list[str], dry_run: bool = False
) -> None:
    """Use rsync to copy a folder.

    Args:
        source: The source folder.
        destination: The destination folder.
        exclude_patterns: A list of patterns to exclude.
        dry_run: If True, will list the files that would be copied without actually copying them.
    """
    source = source.rstrip("/")
    rsync_command = [
        "rsync",
        "-aE",
        "--delete",
        *(f"--exclude={pattern}" for pattern in exclude_patterns),
        f"{source}/",
        destination,
    ]
    if not dry_run:
        subprocess.run(rsync_command, check=True)
    else:
        print(f"Dry run: rsync {source} to {destination} with exclusions {exclude_patterns}")


@with_retries
def create_sparseimage(folder_name: str, source: str) -> None:
    """Create a sparseimage for a folder.

    Args:
        folder_name: The name of the folder to create a sparseimage for.
        source: The source folder.
    """
    sparsebundle_path = f"{folder_name}.sparsebundle"
    resources_for_cleanup["current_sparsebundle"] = sparsebundle_path

    # Remove the sparsebundle if it already exists
    if os.path.exists(sparsebundle_path):
        delete_files(sparsebundle_path, show_output=False)

    hdiutil_command = [
        "hdiutil",
        "create",
        "-srcfolder",
        source,
        "-volname",
        folder_name,
        "-fs",
        "APFS",
        "-format",
        "UDSB",
        sparsebundle_path,
    ]
    subprocess.run(hdiutil_command, check=True)


@with_retries
def convert_sparseimage_to_dmg(folder_name: str, compression_format: str) -> None:
    """Convert a sparseimage to a DMG file.

    Args:
        folder_name: The name of the folder to convert.
        compression_format: The compression format to use.
    """
    output_dmg = f"{folder_name}.dmg"

    # Remove the output DMG if it already exists
    if os.path.exists(output_dmg):
        delete_files(output_dmg, show_output=False)

    hdiutil_command = [
        "hdiutil",
        "convert",
        f"{folder_name}.sparsebundle",
        "-format",
        compression_format,
        "-o",
        output_dmg,
    ]
    subprocess.run(hdiutil_command, check=True)
    delete_files(f"{folder_name}.sparsebundle", show_output=False)


def create_dmg(
    folder_name: str,
    source_folder: str,
    dmg_path: str,
    lzma_compression: bool,
    is_logic: bool,
    dry_run: bool = False,
    force_overwrite: bool = False,
) -> None:
    """Create a DMG file for a folder.

    Args:
        folder_name: The name of the folder to create a DMG for.
        source_folder: The source folder.
        dmg_path: The path to the DMG file to create.
        lzma_compression: If True, will use LZMA compression for the DMG (better but slower).
        is_logic: If True, treats the folder as a Logic Pro project with specific handling.
        dry_run: If True, will list the DMG files that would be created without actually creating them.
        force_overwrite: If True, will overwrite any existing DMG files.
    """
    if dry_run:
        print_colored(
            f"Dry run: Would create DMG {dmg_path} with {'LZMA' if lzma_compression else 'standard'} compression",
            "yellow",
        )
        return

    if os.path.exists(dmg_path):
        if force_overwrite:
            print_colored(f"DMG exists for {folder_name}, overwriting...", "yellow")
            delete_files(dmg_path, show_output=False)
        else:
            print_colored(f"DMG already exists for {folder_name}, skipping.", "yellow")
            return

    temp_dmg_directory = "./temp_dmg"
    resources_for_cleanup["temp_dmg"] = temp_dmg_directory
    intermediary_folder = os.path.join(temp_dmg_directory, folder_name)
    os.makedirs(intermediary_folder, exist_ok=True)

    exclusions = LOGIC_EXCLUSIONS if is_logic else []

    with halo_progress(
        filename=os.path.basename(source_folder),
        start_message="rsyncing",
        end_message="rsynced",
        fail_message="Failed to rsync",
    ):
        rsync_folder(source_folder, intermediary_folder, exclusions, dry_run=dry_run)

    compression_format = "ULMO" if lzma_compression else "UDZO"
    sparsebundle_path = f"{folder_name}.sparsebundle"

    try:
        with halo_progress(
            filename=os.path.basename(folder_name),
            start_message="creating sparseimage for",
            end_message="created sparseimage for",
            fail_message="failed to create sparseimage for",
        ):
            create_sparseimage(folder_name=folder_name, source=intermediary_folder)

        with halo_progress(
            filename=os.path.basename(folder_name),
            start_message="creating DMG for",
            end_message="created DMG for",
            fail_message="failed to create DMG for",
        ):
            convert_sparseimage_to_dmg(
                folder_name=folder_name, compression_format=compression_format
            )

        temp_dmg_path = f"{folder_name}.dmg"
        if dmg_path != temp_dmg_path:
            move_file(temp_dmg_path, dmg_path, overwrite=True)
    finally:
        delete_files(intermediary_folder, show_output=False)
        delete_files(sparsebundle_path, show_output=False)

    print_colored(f"{folder_name} DMG created successfully!", "green")


def process_folders(
    root_dir: str,
    dry_run: bool,
    force_overwrite: bool,
    append_date: bool,
    lzma_compression: bool,
    is_logic: bool,
    exclude_list: list[str],
) -> None:
    """Process folders in the specified directory for DMG creation.

    Args:
        root_dir: The root directory that contains the folders to be processed.
        dry_run: If True, will list the DMG files that would be created without actually creating them.
        force_overwrite: If True, will overwrite any existing DMG files.
        append_date: If True, will append the current date to the DMG file name.
        lzma_compression: If True, will use LZMA compression for the DMG.
        is_logic: If True, treats the folder as a Logic Pro project with specific handling.
        exclude_list: A list of folders to exclude from processing.
    """
    for folder in list_files(root_dir, include_hidden=False):
        folder_path = os.path.join(root_dir, folder)
        if not os.path.isdir(folder_path) or should_exclude(folder, exclude_list):
            continue

        dmg_name = folder
        if append_date:
            today = datetime.now(tz=tz).strftime("%y.%m.%d")
            dmg_name += f" {today}"

        if is_logic:
            logic_extensions = {".logic", ".logicx"}
            is_logic_project = any(
                file.endswith(tuple(logic_extensions)) for file in os.listdir(folder_path)
            )
            if not is_logic_project:
                continue

        dmg_path = os.path.join(root_dir, f"{dmg_name}.dmg")

        if dry_run:
            print(f"Dry run: Would create {dmg_path}")
            continue

        if os.path.exists(dmg_path) and not force_overwrite:
            print_colored(f"DMG already exists for {folder}, skipping.", "yellow")
            continue

        create_dmg(
            folder, folder_path, dmg_path, lzma_compression, is_logic, dry_run, force_overwrite
        )


def cleanup_resources() -> None:
    """Cleanup the resources_for_cleanup if they exist."""
    temp_dmg_directory = resources_for_cleanup.get("temp_dmg")
    current_sparsebundle = resources_for_cleanup.get("current_sparsebundle")

    if temp_dmg_directory and os.path.isdir(temp_dmg_directory):
        delete_files(temp_dmg_directory, show_output=False)

    if current_sparsebundle and os.path.isdir(current_sparsebundle):
        delete_files(current_sparsebundle, show_output=False)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Creates DMG files from folders, with specific handling for Logic project folders."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder to process (default is current directory)",
    )
    parser.add_argument(
        "--logic",
        action="store_true",
        help="Indicate that the folder is a Logic project",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Dry run: list files that would be created",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="Comma-separated list of folder names to exclude",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite DMGs that already exist",
    )
    parser.add_argument(
        "--date",
        action="store_true",
        help="Append current date to the DMG file name",
    )
    parser.add_argument(
        "--lzma",
        action="store_true",
        help="Use LZMA compression for the DMG (better but slower)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Use LZMA compression and append date",
    )
    return parser.parse_args()


def main() -> None:
    """Run the DMG creation."""
    top_level_temp_dmg_directory = None

    try:
        args = parse_arguments()

        original_folder = os.path.abspath(args.folder)
        exclude_list = args.exclude.split(",") if args.exclude else []

        is_current_directory = original_folder == os.path.abspath(".")

        top_level_temp_dmg_directory = os.path.join(original_folder, "temp_dmg")
        if not args.dry_run:
            os.makedirs(top_level_temp_dmg_directory, exist_ok=True)

        if not is_current_directory:
            dmg_name = os.path.basename(original_folder)
            if args.date or args.backup:
                today = datetime.now(tz=tz).strftime("%y.%m.%d")
                dmg_name += f" {today}"
            dmg_path = os.path.join(os.path.dirname(original_folder), f"{dmg_name}.dmg")
            if args.dry_run:
                print(f"Dry run: Would create {dmg_path}")
            else:
                create_dmg(
                    os.path.basename(original_folder),
                    original_folder,
                    dmg_path,
                    args.lzma or args.backup,
                    args.logic,
                    args.dry_run,
                    args.force,
                )
        else:
            process_folders(
                original_folder,
                args.dry_run,
                args.force,
                args.date or args.backup,
                args.lzma or args.backup,
                args.logic,
                exclude_list,
            )

        print_colored("Process completed!", "green")

    except KeyboardInterrupt:
        cleanup_resources()
        print_colored("Cleanup completed. Program interrupted by user.", "red")
        sys.exit(1)
    except Exception as e:
        print_colored(f"An error occurred: {e}", "red")
    finally:
        cleanup_resources()
        if (
            not args.dry_run
            and top_level_temp_dmg_directory
            and os.path.exists(top_level_temp_dmg_directory)
        ):
            delete_files(top_level_temp_dmg_directory, show_output=False)


if __name__ == "__main__":
    main()
