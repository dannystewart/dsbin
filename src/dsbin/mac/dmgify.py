#!/usr/bin/env python3

"""Creates DMG files from folders, with specific handling for Logic projects.

This script creates compressed, read-only DMG (Apple Disk Image) files that preserve all file
metadata, making them ideal for archival and cloud storage. It can process individual folders
or multiple folders at once, with special handling for Logic projects.

Features:
- Creates DMGs that preserve all file metadata (timestamps, permissions, etc.)
- Handles multiple folders: `dmgify *` or `dmgify "Folder A" "Folder B"`
- Processes Logic projects with appropriate exclusions using `--logic`
- Supports custom output names with `-o` or `--output`
- Previews operations with `--dry-run` before making changes

Examples:
    dmgify "My Project"            # Create DMG from a single folder
    dmgify *                       # Process all folders in current directory
    dmgify --logic "Song.logicx"   # Process a Logic project (excludes transient files)
"""

from __future__ import annotations

import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from dsutil import LocalLogger, configure_traceback
from dsutil.argparser import ArgParser
from dsutil.files import delete_files, move_file
from dsutil.progress import halo_progress, with_retries

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterator

configure_traceback()
logger = LocalLogger().get_logger(simple=True)

LOGIC_EXCLUSIONS = [
    "Bounces",
    "Old Bounces",
    "Movie Files",
    "Stems",
]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(
        description="Creates DMG files from folders, with specific handling for Logic project folders.",
        arg_width=36,
    )
    parser.add_argument(
        "folders",
        nargs="*",
        default=["."],
        help="Folders to process (default is current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output DMG filename (without .dmg extension)",
    )
    parser.add_argument(
        "--logic",
        action="store_true",
        help="Process as Logic project (excludes Bounces, Movie Files, etc.)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing DMG files",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="Comma-separated list of folders to exclude",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    return parser.parse_args()


def should_exclude(folder_name: str, exclude_list: list[str]) -> bool:
    """Check if a folder should be excluded."""
    return folder_name in exclude_list


def is_logic_project(folder_path: Path) -> bool:
    """Check if a folder is a Logic project."""
    logic_extensions = {".logic", ".logicx"}
    return any(f.suffix in logic_extensions for f in folder_path.iterdir())


@contextmanager
def temp_workspace() -> Iterator[Path]:
    """Create a temporary workspace for DMG creation.

    Yields:
        Path to the temporary workspace that will be automatically cleaned up.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        try:
            yield temp_path
        finally:
            if temp_path.exists():
                delete_files(temp_path, show_output=False)


def rsync_folder(
    source: Path, destination: Path, exclude_patterns: list[str], dry_run: bool = False
) -> None:
    """Use rsync to create a temporary copy of a folder before creating a disk image from it.

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
        logger.warning(
            "Dry run: rsync %s to %s with exclusions %s.", source, destination, exclude_patterns
        )


@with_retries
def create_sparseimage(folder_name: str, source: Path) -> None:
    """Create a sparseimage for a folder.

    Args:
        folder_name: The name of the folder to create a sparseimage for.
        source: The source folder.
    """
    sparsebundle_path = f"{folder_name}.sparsebundle"

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
def convert_sparseimage_to_dmg(folder_name: str) -> None:
    """Convert a sparseimage to a DMG file."""
    output_dmg = f"{folder_name}.dmg"

    # Remove the output DMG if it already exists
    if Path(output_dmg).exists():
        delete_files(output_dmg, show_output=False)

    hdiutil_command = [
        "hdiutil",
        "convert",
        f"{folder_name}.sparsebundle",
        "-format",
        "ULMO",
        "-o",
        output_dmg,
    ]
    subprocess.run(hdiutil_command, check=True)
    delete_files(f"{folder_name}.sparsebundle", show_output=False)


def create_dmg(
    folder_name: str,
    source_folder: Path,
    dmg_path: Path,
    is_logic: bool,
    dry_run: bool = False,
    force_overwrite: bool = False,
) -> None:
    """Create a DMG file for a folder.

    Args:
        folder_name: The name of the folder to create a DMG for.
        source_folder: The source folder.
        dmg_path: The path to the DMG file to create.
        is_logic: If True, treat the folder as a Logic project with specific handling.
        dry_run: If True, list the DMG files that would be created without actually creating them.
        force_overwrite: If True, overwrite any existing DMG files.
    """
    if dry_run:
        logger.warning("Dry run: Would create DMG %s.", dmg_path)
        return

    if dmg_path.exists():
        if force_overwrite:
            logger.warning("DMG exists for %s, overwriting...", folder_name)
            delete_files(dmg_path, show_output=False)
        else:
            logger.warning("DMG already exists for %s, skipping.", folder_name)
            return

    # Create a clean copy of the source
    with temp_workspace() as workspace:
        intermediary_folder = workspace / folder_name
        intermediary_folder.mkdir()

        exclusions = LOGIC_EXCLUSIONS if is_logic else []

        with halo_progress(
            filename=source_folder.name,
            start_message="Creating temporary copy of",
            end_message="Created temporary copy of",
            fail_message="Failed to copy",
        ):
            rsync_folder(source_folder, intermediary_folder, exclusions, dry_run=dry_run)

        with halo_progress(
            filename=folder_name,
            start_message="Creating sparseimage for",
            end_message="Created sparseimage for",
            fail_message="Failed to create sparseimage for",
        ):
            create_sparseimage(folder_name=folder_name, source=intermediary_folder)

        with halo_progress(
            filename=folder_name,
            start_message="Creating DMG for",
            end_message="Created DMG for",
            fail_message="Failed to create DMG for",
        ):
            convert_sparseimage_to_dmg(folder_name=folder_name)

        temp_dmg = Path(f"{folder_name}.dmg")
        if dmg_path != temp_dmg:
            move_file(temp_dmg, dmg_path, overwrite=True)

    logger.info("%s DMG created successfully!", folder_name)


def process_folder(
    root_dir: Path,
    dry_run: bool,
    force_overwrite: bool,
    is_logic: bool,
    exclude_list: list[str],
    output_name: str | None = None,
) -> None:
    """Process the specified folder for DMG creation.

    Args:
        root_dir: The root directory that contains the folders to be processed.
        dry_run: If True, list the DMG files that would be created without actually creating them.
        force_overwrite: If True, overwrite any existing DMG files.
        is_logic: If True, treats the folder as a Logic project with specific handling.
        exclude_list: A list of folders to exclude from processing.
        output_name: An optional output filename for the DMG file.
    """
    # Return early if not a directory or should be excluded
    if not root_dir.is_dir() or should_exclude(root_dir.name, exclude_list):
        return

    if is_logic and not is_logic_project(root_dir):
        logger.warning("%s is not a Logic project, skipping.", root_dir.name)
        return

    dmg_name = output_name or root_dir.name
    dmg_path = root_dir.parent / f"{dmg_name}.dmg"

    create_dmg(root_dir.name, root_dir, dmg_path, is_logic, dry_run, force_overwrite)


def main() -> None:
    """Run the DMG creation process."""
    try:
        args = parse_arguments()
        exclude_list = args.exclude.split(",") if args.exclude else []

        for folder in args.folders:
            folder_path = Path(folder).resolve()

            if folder_path == Path.cwd():
                # Process all subdirectories in current directory
                for subfolder in folder_path.iterdir():
                    if not subfolder.name.startswith("."):
                        process_folder(
                            root_dir=subfolder,
                            dry_run=args.dry_run,
                            force_overwrite=args.force,
                            is_logic=args.logic,
                            exclude_list=exclude_list,
                            output_name=args.output,
                        )
            else:  # Process single folder
                process_folder(
                    root_dir=folder_path,
                    dry_run=args.dry_run,
                    force_overwrite=args.force,
                    is_logic=args.logic,
                    exclude_list=exclude_list,
                    output_name=args.output,
                )

        logger.info("DMG creation completed!")

    except KeyboardInterrupt:
        logger.error("Process interrupted by user.")
    except Exception as e:
        logger.error("An error occurred: %s", str(e))


if __name__ == "__main__":
    main()
