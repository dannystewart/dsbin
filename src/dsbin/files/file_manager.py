from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from natsort import natsorted
from polykit.cli import confirm_action
from polykit.log import Logician
from send2trash import send2trash

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

# Type alias due to FileManager having a `list` method
PathList = list[Path]


class FileManager:
    """A utility class with a comprehensive set of methods for common file operations.

    It supports listing files with filtering and sorting options, safe file deletion with trash bin
    support, and file copying and moving with overwrite protection. It also includes a method for
    detecting duplicate files using SHA-256 hashing.
    """

    def __init__(
        self,
        log_level: str = "info",
        detailed_log: bool = False,
        logger: Logger | None = None,
    ):
        self.logger = logger or Logician.get_logger(level=log_level, simple=not detailed_log)

    def list(
        self,
        dir: Path,  # noqa: A002
        exts: str | list[str] | None = None,
        recursive: bool = False,
        exclude: str | list[str] | None = None,
        include_hidden: bool = False,
        sort_key: Callable[..., Any] | None = None,
        reverse_sort: bool = False,
    ) -> list[Path]:
        """List all files in a directory that match the given criteria.

        Sorting is performed by modification time in ascending order by default. Customize sorting
        with the 'sort_key' and 'reverse' parameters.

        Args:
            dir: The directory to search.
            exts: The file extensions to include. If None, all files will be included.
            recursive: Whether to search recursively.
            exclude: Glob patterns to exclude.
            include_hidden: Whether to include hidden files.
            sort_key: A function to use for sorting the files.
            reverse_sort: Whether to reverse the sort order.

        Returns:
            A list of file paths as Path objects.

        Example usage with custom sort (alphabetical sorting by file name):
            `file_list = files.list(dir, sort_key=lambda x: x.stat().st_mtime)`
        """
        if exts:
            # Handle both single string and list inputs
            ext_list = [exts] if isinstance(exts, str) else exts
            # Handle extensions with or without dots
            ext_list = [ext.lstrip(".") for ext in ext_list]
            glob_patterns = [f"*.{ext}" for ext in ext_list]
        else:
            glob_patterns = ["*"]

        files_filtered: list[Path] = []
        for pattern in glob_patterns:
            files = dir.rglob(pattern) if recursive else dir.glob(pattern)
            try:
                files_filtered.extend(
                    file
                    for file in files
                    if file.is_file()
                    and (include_hidden or not file.name.startswith("."))
                    and not (exclude and any(file.match(pattern) for pattern in exclude))
                )
            except FileNotFoundError:
                self.logger.error(
                    "Error accessing file while searching %s: File not found", pattern
                )

        sort_function = sort_key or (lambda x: x.stat().st_mtime)
        return natsorted(files_filtered, key=sort_function, reverse=reverse_sort)

    def delete(
        self,
        file_paths: Path | PathList,
        show_output: bool = True,
        show_individual: bool = True,
        show_total: bool = True,
        dry_run: bool = False,
    ) -> tuple[int, int]:
        """Safely move a list of files to the trash. If that fails, asks for confirmation and
        deletes them directly.

        Args:
            file_paths: The file paths to delete.
            show_output: Whether to print output. (This overrides show_individual and show_total.)
            show_individual: Whether to print output for each individual file.
            show_total: Whether to print the total number of files deleted at the end.
            dry_run: Whether to do a dry run (don't actually delete).

        Returns:
            The number of successful deletions and failed deletions.
        """
        if dry_run and show_output:
            self.logger.warning("NOTE: Dry run, not actually deleting!")

        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        successful_deletions, failed_deletions = 0, 0

        for file_path in file_paths:
            if not file_path.exists():
                failed_deletions += 1
                if show_individual and show_output:
                    self.logger.warning("File %s does not exist.", file_path.name)
                continue

            if self._handle_file_deletion(
                file_path, dry_run=dry_run, show_output=show_individual and show_output
            ):
                successful_deletions += 1
            else:
                failed_deletions += 1

        if show_total and show_output and not dry_run:
            message = (
                f"{successful_deletions} file{'s' if successful_deletions != 1 else ''} trashed."
            )
            if failed_deletions > 0:
                message += f" Failed to delete {failed_deletions} file{'s' if failed_deletions != 1 else ''}."
            self.logger.info(message)

        return successful_deletions, failed_deletions

    def copy(
        self,
        source: Path,
        destination: Path,
        overwrite: bool = True,
        show_output: bool = True,
    ) -> bool:
        """Copy a file from source to destination.

        Args:
            source: The source file path.
            destination: The destination file path.
            overwrite: Whether to overwrite the destination file if it already exists.
            show_output: Whether to print output.
        """
        try:
            if not overwrite and destination.exists():
                if show_output:
                    self.logger.warning(
                        "Error: Destination file %s already exists. Use overwrite=True to overwrite it.",
                        destination,
                    )
                return False

            if sys.platform == "win32":
                self._copy_win32_file(source, destination)
            else:
                shutil.copy2(source, destination)

            if show_output:
                self.logger.info("Copied %s to %s.", source, destination)
            return True
        except Exception as e:
            if show_output:
                self.logger.error("Error copying file: %s", str(e))
            return False

    def move(
        self,
        source: Path,
        destination: Path,
        overwrite: bool = False,
        show_output: bool = True,
    ) -> bool:
        """Move a file from source to destination.

        Args:
            source: The source file path.
            destination: The destination file path.
            overwrite: Whether to overwrite the destination file if it already exists.
            show_output: Whether to print output.
        """
        try:
            if not overwrite and destination.exists():
                if show_output:
                    self.logger.warning(
                        "Error: Destination file %s already exists. Use overwrite=True to overwrite it.",
                        destination,
                    )
                return False

            shutil.move(str(source), str(destination))
            if show_output:
                self.logger.info("Moved %s to %s.", source, destination)
            return True
        except Exception as e:
            self.logger.error("Error moving file: %s", str(e))
            return False

    def find_dupes_by_hash(self, files: PathList) -> None:
        """Find and print duplicate files by comparing their SHA-256 hashes.

        Args:
            files: A list of file paths.
        """
        hash_map = {}
        duplicates_found = False

        for file_path in files:
            if file_path.is_file():
                file_hash = self.sha256_checksum(file_path)
                if file_hash not in hash_map:
                    hash_map[file_hash] = [file_path]
                else:
                    hash_map[file_hash].append(file_path)
                    duplicates_found = True

        for file_hash, file_list in hash_map.items():
            if len(file_list) > 1:
                self.logger.info("\nHash: %s", file_hash)
                self.logger.warning("Duplicate files:")
                for duplicate_file in file_list:
                    self.logger.info("  - %s", duplicate_file)

        if not duplicates_found:
            self.logger.info("No duplicates found!")

    def _handle_file_deletion(
        self,
        file_path: Path,
        dry_run: bool = False,
        show_output: bool = True,
    ) -> bool:
        """Attempt to delete a single file, sending it to trash or permanently deleting it.

        Args:
            file_path: The path of the file to delete.
            dry_run: Whether to perform a dry run.
            show_output: Whether to print output messages.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        try:
            if dry_run:
                if show_output:
                    self.logger.info("Would delete: %s", file_path)
                return True

            send2trash(str(file_path))
            if show_output:
                self.logger.info("✔ Trashed %s", file_path.name)
            return True
        except Exception as e:
            if show_output:
                self.logger.error("Failed to send file to trash: %s", str(e))
            if confirm_action("Do you want to permanently delete the file?"):
                try:
                    file_path.unlink()
                    if show_output:
                        self.logger.info("✔ Permanently deleted %s", file_path.name)
                    return True
                except OSError as err:
                    if show_output:
                        self.logger.error(
                            "Error: Failed to permanently delete %s : %s", file_path.name, err
                        )
        return False

    @staticmethod
    def get_timestamps(file: Path) -> tuple[str, str]:
        """Get file creation and modification timestamps. macOS only, as it relies on GetFileInfo.

        Returns:
            ctime: The creation timestamp.
            mtime: The modification timestamp.
        """
        ctime = subprocess.check_output(["GetFileInfo", "-d", str(file)]).decode().strip()
        mtime = subprocess.check_output(["GetFileInfo", "-m", str(file)]).decode().strip()
        return ctime, mtime

    @staticmethod
    def set_timestamps(file: Path, ctime: str | None = None, mtime: str | None = None) -> None:
        """Set file creation and/or modification timestamps. macOS only, as it relies on SetFile.

        Args:
            file: The file to set the timestamps on.
            ctime: The creation timestamp to set. If None, creation time won't be set.
            mtime: The modification timestamp to set. If None, modification time won't be set.

        Raises:
            ValueError: If both ctime and mtime are None.
        """
        if ctime is None and mtime is None:
            msg = "At least one of ctime or mtime must be set."
            raise ValueError(msg)
        if ctime:
            subprocess.run(["SetFile", "-d", ctime, str(file)], check=False)
        if mtime:
            subprocess.run(["SetFile", "-m", mtime, str(file)], check=False)

    @staticmethod
    def compare_mtime(file1: Path, file2: Path) -> float:
        """Compare two files based on modification time.

        Args:
            file1: The first file path.
            file2: The second file path.

        Returns:
            The difference in modification time between the two files as a float.
        """
        stat1 = file1.stat()
        stat2 = file2.stat()
        return stat1.st_mtime - stat2.st_mtime

    @staticmethod
    def sha256_checksum(filename: Path, block_size: int = 65536) -> str:
        """Generate SHA-256 hash of a file.

        Args:
            filename: The file path.
            block_size: The block size to use when reading the file. Defaults to 65536.

        Returns:
            The SHA-256 hash of the file.
        """
        sha256 = hashlib.sha256()
        with filename.open("rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                sha256.update(block)
        return sha256.hexdigest()
