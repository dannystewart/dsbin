#!/usr/bin/env python3

"""Creates DMG files from folders, with specific handling for Logic projects.

This script creates compressed, read-only DMG (Apple Disk Image) files that preserve all file
metadata, making them ideal for archival and cloud storage. It can process individual folders
or multiple folders at once, with special handling for Logic projects.

By default, it will store the contents of the folder directly at the root of the DMG. However, you
can preserve the top level folder by using the `-p` or `--preserve-folder` option. This stores the
entire contents within a named subfolder on the disk image, which makes copying easier.

Features:
- Creates DMGs that preserve all file metadata (timestamps, permissions, etc.)
- Handles multiple folders: `dmgify *` or `dmgify "Folder A" "Folder B"`
- Processes Logic projects with appropriate exclusions using `--logic`
- Supports custom output names with `-o` or `--output`
- Can overwrite existing DMGs with `-f` or `--force`
- Can preserve the top level folder in the DMG with `p` or `--preserve-folder`
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
from typing import TYPE_CHECKING, ClassVar

from dsutil import LocalLogger, configure_traceback
from dsutil.argparser import ArgParser
from dsutil.files import delete_files, move_file
from dsutil.progress import halo_progress, with_retries

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterator

configure_traceback()
logger = LocalLogger().get_logger(simple=True)


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


class DMGCreator:
    """Creates DMG files from folders."""

    DEFAULT_EXCLUSIONS: ClassVar[list[str]] = [
        ".DS_Store",
        "._*",
        ".Spotlight-V*",
        ".fseventsd",
        ".Trashes",
    ]
    LOGIC_EXCLUSIONS: ClassVar[list[str]] = [
        "Bounces",
        "Old Bounces",
        "Movie Files",
        "Stems",
    ]

    def __init__(
        self,
        dry_run: bool = False,
        force_overwrite: bool = False,
        is_logic: bool = False,
        exclude_list: list[str] | None = None,
        output_name: str | None = None,
        preserve_folder: bool = False,
    ) -> None:
        """Initialize DMG creator with configuration options."""
        self.dry_run = dry_run
        self.force_overwrite = force_overwrite
        self.is_logic = is_logic
        self.exclude_list = exclude_list or []
        self.output_name = output_name
        self.preserve_folder = preserve_folder

    def rsync_folder(self, source: Path, destination: Path) -> None:
        """Create a temporary copy of a folder."""
        source = Path(str(source).rstrip("/"))
        exclusions = [*self.DEFAULT_EXCLUSIONS]  # Start with default exclusions
        if self.is_logic:
            exclusions.extend(self.LOGIC_EXCLUSIONS)  # Add Logic exclusions if needed

        # If preserving the top level folder, copy to a subdirectory
        target = destination / source.name if self.preserve_folder else destination

        if self.preserve_folder:
            target.mkdir(parents=True)

        rsync_command = [
            "rsync",
            "-aE",
            "--delete",
            *(f"--exclude={pattern}" for pattern in exclusions),
            f"{source}/",
            target,
        ]
        if not self.dry_run:
            subprocess.run(rsync_command, check=True)
        else:
            logger.warning(
                "Dry run: rsyncing '%s' to '%s'%s",
                source,
                target,
                f" with exclusions: {exclusions}" if exclusions else "",
            )

    def create_dmg(self, folder_path: Path) -> None:
        """Create a DMG file for a folder."""
        folder_name = folder_path.name
        dmg_name = self.output_name or folder_name
        dmg_path = folder_path.parent / f"{dmg_name}.dmg"

        if self.dry_run:
            logger.warning("Dry run: Would create DMG %s", dmg_path)
            return

        if dmg_path.exists():
            if self.force_overwrite:
                logger.warning("%s already exists, but forcing overwrite.", dmg_path.name)
                delete_files(dmg_path, show_output=False)
            else:
                logger.warning("%s already exists, skipping.", dmg_path.name)
                return

        with temp_workspace() as workspace:
            intermediary_folder = workspace / folder_name
            intermediary_folder.mkdir()

            with halo_progress(
                filename=folder_path.name,
                start_message="Creating temporary copy of folder:",
                end_message="Created temporary copy of folder:",
                fail_message="Failed to copy folder:",
            ):
                self.rsync_folder(folder_path, intermediary_folder)

            with halo_progress(
                filename=folder_name,
                start_message="Creating sparseimage for",
                end_message="Created sparseimage for",
                fail_message="Failed to create sparseimage for",
            ):
                self._create_sparseimage(folder_name, intermediary_folder)

            with halo_progress(
                filename=folder_name,
                start_message="Creating DMG for",
                end_message="Created DMG for",
                fail_message="Failed to create DMG for",
            ):
                self._convert_sparseimage_to_dmg(folder_name)

            temp_dmg = Path(f"{folder_name}.dmg")
            if dmg_path != temp_dmg:
                move_file(temp_dmg, dmg_path, overwrite=True, show_output=False)

        logger.info("Successfully created DMG: %s", dmg_path.name)

    @with_retries
    def _create_sparseimage(self, folder_name: str, source: Path) -> None:
        sparsebundle_path = f"{folder_name}.sparsebundle"
        if Path(sparsebundle_path).exists():
            delete_files(sparsebundle_path, show_output=False)

        subprocess.run(
            [
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
            ],
            check=True,
        )

    @with_retries
    def _convert_sparseimage_to_dmg(self, folder_name: str) -> None:
        output_dmg = f"{folder_name}.dmg"
        if Path(output_dmg).exists():
            delete_files(output_dmg, show_output=False)

        subprocess.run(
            [
                "hdiutil",
                "convert",
                f"{folder_name}.sparsebundle",
                "-format",
                "ULMO",
                "-o",
                output_dmg,
            ],
            check=True,
        )
        delete_files(f"{folder_name}.sparsebundle", show_output=False)

    def process_folders(self, folders: list[str]) -> None:
        """Process multiple folders for DMG creation."""
        for folder in folders:
            folder_path = Path(folder).resolve()

            if folder_path == Path.cwd():
                # Process all subdirectories in current directory
                for subfolder in folder_path.iterdir():
                    if not subfolder.name.startswith("."):
                        self.process_folder(subfolder)
            else:  # Process single folder
                self.process_folder(folder_path)

    def process_folder(self, folder_path: Path) -> None:
        """Process a folder for DMG creation."""
        if not folder_path.is_dir() or self._should_exclude(folder_path.name):
            return

        if self.is_logic and not self._is_logic_project(folder_path):
            logger.warning("'%s' is not a Logic project, skipping.", folder_path.name)
            return

        self.create_dmg(folder_path)

    def _should_exclude(self, folder_name: str) -> bool:
        return folder_name in self.exclude_list

    @staticmethod
    def _is_logic_project(folder_path: Path) -> bool:
        logic_extensions = {".logic", ".logicx"}
        return any(f.suffix in logic_extensions for f in folder_path.iterdir())


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
        "-p",
        "--preserve-folder",
        action="store_true",
        help="Keep the top-level folder in the DMG (default is to flatten)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    return parser.parse_args()


def main() -> None:
    """Run the DMG creation process."""
    try:
        args = parse_arguments()
        exclude_list = args.exclude.split(",") if args.exclude else None

        creator = DMGCreator(
            dry_run=args.dry_run,
            force_overwrite=args.force,
            is_logic=args.logic,
            exclude_list=exclude_list,
            output_name=args.output,
            preserve_folder=args.preserve_folder,
        )

        creator.process_folders(args.folders)
        logger.info("Processing complete!")

    except KeyboardInterrupt:
        logger.error("Process interrupted by user.")
    except Exception as e:
        logger.error("An error occurred: %s", str(e))


if __name__ == "__main__":
    main()
