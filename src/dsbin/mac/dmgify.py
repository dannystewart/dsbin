#!/usr/bin/env python3

"""Creates DMG files from folders, with specific handling for Logic projects.

This script automates the creation of DMG (Apple Disk Image) files from directories for archival and
backup. It has additional functionality to handle Logic project folders with appropriate
exclusions and compression options to optimize the disk images for storage.

Features:

- Processes individual directories or batch processes all directories within a specified path.
- Handles directories as Logic projects with the `--logic` flag, excluding non-essential subfolders.
- Offers LZMA compression with the `--lzma` flag for smaller but slower-to-create DMGs.
- Allows datestamping of DMG filenames with the `--date` flag, useful for versioning.
- Supports the `--backup` flag, combining LZMA compression and date appending in one option.
- Excludes specified directories with the `--exclude` flag, taking a comma-separated list.
- Overwrites existing DMG files if `--force` is specified, otherwise skips existing files.
- Performs a dry run with `--dry-run`, which will output expected filenames without generating them.

The script ensures a clean state by creating a temporary folder to store interim files
during the creation process and performs cleanup of these resources on completion or failure.

Usage:

To create DMGs for all folders in the current directory, just run the script without any arguments.
Specify a folder by providing its path to process only that directory. Use the provided flags
(`--logic`, `--lzma`, `--date`, `--backup`, `--exclude`, and `--force`) to control the script's
behavior, or use `--help` to view all available options.
"""

from __future__ import annotations

import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from dsutil import LocalLogger, configure_traceback
from dsutil.argparser import ArgParser
from dsutil.files import delete_files, list_files, move_file
from dsutil.progress import halo_progress, with_retries

if TYPE_CHECKING:
    import argparse
    import types

configure_traceback()

tz = ZoneInfo("America/New_York")

LOGIC_EXCLUSIONS = ["Bounces", "Old Bounces", "Movie Files", "Stems"]

resources_for_cleanup: dict[str, Path | None] = {
    "temp_dmg": None,
    "current_sparsebundle": None,
}


def signal_handler(signum: int | None = None, frame: types.FrameType | None = None) -> None:  # noqa: ARG001
    """Handle signals and cleanup resources."""
    cleanup_resources(is_cancel=True)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

logger = LocalLogger().get_logger(simple=True)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(
        description="Creates DMG files from folders, with specific handling for Logic project folders.",
        arg_width=36,
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


def cleanup_resources(is_cancel: bool = False) -> None:
    """Cleanup the resources_for_cleanup if they exist."""
    temp_dmg_directory = resources_for_cleanup.get("temp_dmg")
    current_sparsebundle = resources_for_cleanup.get("current_sparsebundle")

    if temp_dmg_directory and temp_dmg_directory.is_dir():
        delete_files(temp_dmg_directory, show_output=False)

    if current_sparsebundle and current_sparsebundle.is_dir():
        delete_files(current_sparsebundle, show_output=False)

    if is_cancel:
        logger.error("Program interrupted. Temp files cleaned up.")
        sys.exit(1)


def should_exclude(folder_name: str, exclude_list: list[str]) -> bool:
    """Check if a folder should be excluded."""
    return folder_name in exclude_list


def rsync_folder(
    source: Path, destination: Path, exclude_patterns: list[str], dry_run: bool = False
) -> None:
    """Use rsync to copy a folder.

    Args:
        source: The source folder.
        destination: The destination folder.
        exclude_patterns: A list of patterns to exclude.
        dry_run: If True, list the files that would be copied without actually copying them.
    """
    source = Path(str(source).rstrip("/"))
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
def create_sparseimage(folder_name: str, source: Path) -> None:
    """Create a sparseimage for a folder.

    Args:
        folder_name: The name of the folder to create a sparseimage for.
        source: The source folder.
    """
    sparsebundle_path = f"{folder_name}.sparsebundle"
    resources_for_cleanup["current_sparsebundle"] = Path(sparsebundle_path)

    # Remove the sparsebundle if it already exists
    if Path(sparsebundle_path).exists():
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
    if Path(output_dmg).exists():
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
    source_folder: Path,
    dmg_path: Path,
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
        lzma_compression: If True, use LZMA compression for the DMG (better but slower).
        is_logic: If True, treat the folder as a Logic project with specific handling.
        dry_run: If True, list the DMG files that would be created without actually creating them.
        force_overwrite: If True, overwrite any existing DMG files.
    """
    if dry_run:
        logger.warning(
            "Dry run: Would create DMG %s with %s compression",
            dmg_path,
            "LZMA" if lzma_compression else "standard",
        )
        return

    if Path(dmg_path).exists():
        if force_overwrite:
            logger.warning("DMG exists for %s, overwriting...", folder_name)
            delete_files(dmg_path, show_output=False)
        else:
            logger.warning("DMG already exists for %s, skipping.", folder_name)
            return

    temp_dmg_directory = "./temp_dmg"
    resources_for_cleanup["temp_dmg"] = Path(temp_dmg_directory)
    intermediary_folder = Path(temp_dmg_directory) / folder_name
    Path(intermediary_folder).mkdir(parents=True, exist_ok=True)

    exclusions = LOGIC_EXCLUSIONS if is_logic else []

    with halo_progress(
        filename=Path(source_folder).name,
        start_message="Creating temporary copy of",
        end_message="Copied",
        fail_message="Failed to copy",
    ):
        rsync_folder(source_folder, intermediary_folder, exclusions, dry_run=dry_run)

    compression_format = "ULMO" if lzma_compression else "UDZO"
    sparsebundle_path = f"{folder_name}.sparsebundle"

    try:
        with halo_progress(
            filename=Path(folder_name).name,
            start_message="Creating sparseimage for",
            end_message="Created sparseimage for",
            fail_message="Failed to create sparseimage for",
        ):
            create_sparseimage(folder_name=folder_name, source=intermediary_folder)

        with halo_progress(
            filename=Path(folder_name).name,
            start_message="Creating DMG for",
            end_message="Created DMG for",
            fail_message="Failed to create DMG for",
        ):
            convert_sparseimage_to_dmg(
                folder_name=folder_name, compression_format=compression_format
            )

        temp_dmg_path = Path(f"{folder_name}.dmg")
        if dmg_path != temp_dmg_path:
            move_file(temp_dmg_path, dmg_path, overwrite=True)
    finally:
        delete_files(intermediary_folder, show_output=False)
        delete_files(sparsebundle_path, show_output=False)

    logger.info("%s DMG created successfully!", folder_name)


def process_folders(
    root_dir: Path,
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
        dry_run: If True, list the DMG files that would be created without actually creating them.
        force_overwrite: If True, overwrite any existing DMG files.
        append_date: If True, append the current date to the DMG file name.
        lzma_compression: If True, use LZMA compression for the DMG.
        is_logic: If True, treats the folder as a Logic project with specific handling.
        exclude_list: A list of folders to exclude from processing.
    """
    for folder in list_files(root_dir, include_hidden=False):
        folder_path = root_dir / folder
        if not Path(folder_path).is_dir() or should_exclude(folder, exclude_list):
            continue

        dmg_name = folder
        if append_date:
            today = datetime.now(tz=tz).strftime("%y.%m.%d")
            dmg_name += f" {today}"

        if is_logic:
            logic_extensions = {".logic", ".logicx"}
            is_logic_project = any(
                Path(file).suffix in logic_extensions for file in list_files(folder_path)
            )
            if not is_logic_project:
                continue

        dmg_path = Path(root_dir) / f"{dmg_name}.dmg"

        if dry_run:
            print(f"Dry run: Would create {dmg_path}")
            continue

        if Path(dmg_path).exists() and not force_overwrite:
            logger.warning("DMG already exists for %s, skipping.", folder)
            continue

        create_dmg(
            folder, folder_path, dmg_path, lzma_compression, is_logic, dry_run, force_overwrite
        )


def handle_current_dir(args: argparse.Namespace, original_folder: Path) -> None:
    """Handle the current directory as a Logic project or regular folder."""
    dmg_name = Path(original_folder).name
    if args.date or args.backup:
        today = datetime.now(tz=tz).strftime("%y.%m.%d")
        dmg_name += f" {today}"
    dmg_path = Path(original_folder).parent / f"{dmg_name}.dmg"
    if args.dry_run:
        print(f"Dry run: Would create {dmg_path}")
    else:
        create_dmg(
            Path(original_folder).name,
            original_folder,
            dmg_path,
            args.lzma or args.backup,
            args.logic,
            args.dry_run,
            args.force,
        )


def handle_logic_project_dir(args: argparse.Namespace, original_folder: Path) -> bool:
    """Handle a Logic project directory."""
    if args.logic:
        logic_extensions = {".logic", ".logicx"}
        if any(Path(file).suffix in logic_extensions for file in list_files(original_folder)):
            dmg_name = original_folder.name
            if args.date or args.backup:
                today = datetime.now(tz=tz).strftime("%y.%m.%d")
                dmg_name += f" {today}"
            dmg_path = original_folder.parent / f"{dmg_name}.dmg"
            if args.dry_run:
                logger.warning("Dry run: Would create %s", str(dmg_path))
            else:
                create_dmg(
                    original_folder.name,
                    original_folder,
                    dmg_path,
                    args.lzma or args.backup,
                    True,
                    args.dry_run,
                    args.force,
                )
            logger.info("Process completed!")
            return True
    return False


def main() -> None:
    """Run the DMG creation.

    Raises:
        SystemExit: If the user provides invalid arguments.
    """
    try:
        args = parse_arguments()
    except SystemExit:
        return

    top_level_temp_dmg_directory = None

    try:
        original_folder = Path(args.folder).resolve()
        exclude_list = args.exclude.split(",") if args.exclude else []

        is_current_directory = original_folder == Path.cwd()

        top_level_temp_dmg_directory = Path(original_folder) / "temp_dmg"
        if not args.dry_run:
            Path(top_level_temp_dmg_directory).mkdir(parents=True, exist_ok=True)

        if not is_current_directory:
            handle_current_dir(args, original_folder)
        else:
            # If --logic is specified, first check if current directory is a Logic project
            if handle_logic_project_dir(args, original_folder):
                return

            # If we get here, either --logic wasn't specified or directory isn't a Logic project
            process_folders(
                original_folder,
                args.dry_run,
                args.force,
                args.date or args.backup,
                args.lzma or args.backup,
                args.logic,
                exclude_list,
            )

        logger.info("Process completed!")

    except SystemExit:
        raise
    except KeyboardInterrupt:
        cleanup_resources(is_cancel=True)
    except Exception as e:
        logger.error("An error occurred: %s", str(e))
    finally:
        cleanup_resources()
        if (
            args
            and not args.dry_run
            and top_level_temp_dmg_directory
            and Path(top_level_temp_dmg_directory).exists()
        ):
            delete_files(top_level_temp_dmg_directory, show_output=False)


if __name__ == "__main__":
    main()
