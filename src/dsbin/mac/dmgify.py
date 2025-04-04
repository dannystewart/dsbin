#!/usr/bin/env python3

"""Creates DMG files from folders, with specific handling for Logic projects.

This script creates compressed, read-only DMG (Apple Disk Image) files that preserve all file
metadata, making them ideal for archival and cloud storage. It can process individual folders
or multiple folders at once, with special handling for Logic projects.

By default, it will store the contents of the folder directly at the root of the DMG. However, you
can preserve the top level folder by using the `-p` or `--preserve-folder` option. This stores the
full contents within a named subfolder on the disk image, which makes it easier to copy everything.

Features:
- Creates DMGs that preserve all file metadata (timestamps, permissions, etc.)
- Handles multiple folders: `dmgify *` or `dmgify "Folder A" "Folder B"`
- Processes Logic projects with appropriate exclusions using `--logic`
- Supports custom output names with `-o` or `--output`
- Can overwrite existing DMGs with `-f` or `--force`
- Can preserve the top level folder in the DMG with `p` or `--preserve-folder`

Examples:
    dmgify "My Project"            # Create DMG from a single folder
    dmgify *                       # Process all folders in current directory
    dmgify --logic "Song.logicx"   # Process a Logic project (excludes transient files)
"""

from __future__ import annotations

import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from logician import Logician
from polykit import polykit_setup
from polykit.cli import ArgParser, halo_progress
from polykit.core import with_retries
from polykit.shell import handle_interrupt

from dsbin.files import FileManager

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterator
    from logging import Logger

polykit_setup()


@contextmanager
def temp_workspace() -> Iterator[Path]:
    """Create a temporary workspace for DMG creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        try:
            yield temp_path
        finally:
            if temp_path.exists():
                FileManager().delete(temp_path, show_output=False)


@dataclass
class DMGCreator:
    """Creates DMG files from folders.

    Args:
        force_overwrite: Overwrite existing DMG files if they exist.
        is_logic: Treat as a Logic project (excludes folders listed in LOGIC_EXCLUSIONS).
        exclude_list: Comma-separated list of folders to exclude.
        output_name: Output DMG filename (without extension).
        preserve_folder: Whether to preserve and keep contents in the top-level folder at the root.
    """

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

    force_overwrite: bool = False
    is_logic: bool = False
    exclude_list: list[str] = field(default_factory=list)
    output_name: str | None = None
    preserve_folder: bool = False

    exclusions: list[str] = field(init=False)
    files: FileManager = field(init=False)
    logger: Logger = field(init=False)

    def __post_init__(self):
        self.logger = Logician.get_logger(simple=True)
        self.files = FileManager(logger=self.logger)

        # Always preserve top-level folder for Logic projects
        if self.is_logic:
            self.logger.info("* Processing as Logic project.")
            self.preserve_folder = True

        if self.preserve_folder:
            self.logger.info("* Preserving top-level folder.")

        # Build exclusion list based on DMG type
        self.exclusions = [*self.DEFAULT_EXCLUSIONS]
        if self.is_logic:
            self.exclusions.extend(self.LOGIC_EXCLUSIONS)

    def create_dmg(self, folder_path: Path) -> None:
        """Create a DMG file for a folder."""
        folder_name = folder_path.name
        dmg_name = self.output_name or folder_name
        dmg_path = folder_path.parent / f"{dmg_name}.dmg"

        if dmg_path.exists():
            if self.force_overwrite:
                self.logger.warning("%s already exists, but forcing overwrite.", dmg_path.name)
                self.files.delete(dmg_path, show_output=False)
            else:
                self.logger.warning("%s already exists, skipping.", dmg_path.name)
                return

        with temp_workspace() as workspace:
            intermediary_folder = workspace / folder_name
            intermediary_folder.mkdir()

            with halo_progress(
                folder_path.name,
                start_message="Creating temporary copy of folder:",
                end_message="Created temporary copy of folder:",
                fail_message="Failed to copy folder:",
            ):
                self._rsync_folder(folder_path, intermediary_folder)

            with halo_progress(
                folder_name,
                start_message="Creating sparseimage for",
                end_message="Created sparseimage for",
                fail_message="Failed to create sparseimage for",
            ):
                self._create_sparseimage(folder_name, intermediary_folder)

            with halo_progress(
                folder_name,
                start_message="Creating DMG for",
                end_message="Created DMG for",
                fail_message="Failed to create DMG for",
            ):
                self._convert_sparseimage_to_dmg(folder_name)

            temp_dmg = Path(f"{folder_name}.dmg")
            if dmg_path != temp_dmg:
                self.files.move(temp_dmg, dmg_path, overwrite=True, show_output=False)

        self.logger.info("Successfully created DMG: %s", dmg_path.name)

    def _rsync_folder(self, source: Path, destination: Path) -> None:
        source = Path(str(source).rstrip("/"))

        # If preserving the top level folder, copy to a subdirectory
        target = destination / source.name if self.preserve_folder else destination

        if self.preserve_folder:
            target.mkdir(parents=True)

        rsync_command = [
            "rsync",
            "-aE",
            "--delete",
            *(f"--exclude={pattern}" for pattern in self.exclusions),
            f"{source}/",
            target,
        ]
        subprocess.run(rsync_command, check=True)

    @with_retries
    def _create_sparseimage(self, folder_name: str, source: Path) -> None:
        sparsebundle_path = Path(f"{folder_name}.sparsebundle")
        if sparsebundle_path.exists():
            self.files.delete(sparsebundle_path, show_output=False)

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
        output_dmg = Path(f"{folder_name}.dmg")
        if Path(output_dmg).exists():
            self.files.delete(output_dmg, show_output=False)

        sparsebundle = Path(f"{folder_name}.sparsebundle")
        subprocess.run(
            ["hdiutil", "convert", sparsebundle, "-format", "ULMO", "-o", output_dmg],
            check=True,
        )
        self.files.delete(sparsebundle, show_output=False)

    def process_folders(self, folders: list[str]) -> None:
        """Process multiple folders for DMG creation."""
        for folder in folders:
            try:
                folder_path = Path(folder).resolve()

                if folder_path == Path.cwd():
                    # Process all subdirectories in current directory
                    for subfolder in folder_path.iterdir():
                        if not subfolder.name.startswith("."):
                            self.process_folder(subfolder)
                else:  # Process single folder
                    self.process_folder(folder_path)

            except Exception as e:
                self.logger.error("Error processing '%s': %s", folder, str(e))
                continue

        self.logger.info("Processing complete!")

    def process_folder(self, folder_path: Path) -> None:
        """Process a folder for DMG creation."""
        if not folder_path.is_dir() or self._should_exclude(folder_path.name):
            return

        if self.is_logic and not self._is_logic_project(folder_path):
            self.logger.warning("'%s' is not a Logic project, skipping.", folder_path.name)
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
        help="folders to process (defaults to current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output filename (without extension)",
    )
    parser.add_argument(
        "--logic",
        action="store_true",
        help="handle as Logic project (exclude Bounces, Movie Files, Stems)",
    )
    parser.add_argument(
        "-p",
        "--preserve-folder",
        action="store_true",
        help="preserve top-level folder at root (flattens by default)",
    )
    parser.add_argument("-e", "--exclude", help="comma-separated list of folders to exclude")
    parser.add_argument("-f", "--force", action="store_true", help="overwrite existing files")
    return parser.parse_args()


@handle_interrupt()
def main() -> None:
    """Run the DMG creation process."""
    args = parse_arguments()
    exclude_list: list[str] = args.exclude.split(",") if args.exclude else []

    creator = DMGCreator(
        force_overwrite=args.force,
        is_logic=args.logic,
        exclude_list=exclude_list,
        output_name=args.output,
        preserve_folder=args.preserve_folder,
    )
    creator.process_folders(args.folders)


if __name__ == "__main__":
    main()
