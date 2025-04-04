#!/usr/bin/env python3

"""Generate large files to fill the disk and free up purgeable space.

This script will create dummy files in a specified location until the free space available
on the drive is below a specified threshold, then delete the created files and check the
free space again. macOS is kind of stupid about freeing up large amounts of space, so this
script is a workaround to force it to clean up without having to reboot.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from logician import Logician
from polykit import polykit_setup
from polykit.cli import halo_progress
from polykit.shell import handle_interrupt

if TYPE_CHECKING:
    from types import FrameType

polykit_setup()

logger = Logician.get_logger()

# macOS becomes unstable with less than 20GB of free space
MIN_FREE_SPACE_GB = 20


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fill disk until minimum free space to force macOS to free purgeable space"
    )
    parser.add_argument(
        "-s",
        "--space",
        type=float,
        default=MIN_FREE_SPACE_GB,
        help=f"minimum free space in GB to maintain (default: {MIN_FREE_SPACE_GB})",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        default="/tmp/largefiles",
        help="directory to store temp files (default: /tmp/largefiles)",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        default="/System/Volumes/Data",
        help="path to check disk usage (default: /System/Volumes/Data)",
    )
    args = parser.parse_args()

    # Ensure minimum free space for safety
    if args.space < MIN_FREE_SPACE_GB:
        logger.warning(
            "Minimum free space set below safe threshold. Using %s GB instead.", MIN_FREE_SPACE_GB
        )
        args.space = MIN_FREE_SPACE_GB

    return args


def format_space_in_gb(bytes_amount: int) -> str:
    """Format bytes into a human-readable GB value."""
    return f"{bytes_amount / (1024 * 1024 * 1024):.2f} GB"


def get_free_space(path: Path) -> int:
    """Get free space in bytes for the specified path."""
    _, _, free = shutil.disk_usage(path)
    return free


def get_disk_usage(path: Path) -> int:
    """Get the current disk usage percentage for the specified path."""
    result = subprocess.run(["df", "-k", path], capture_output=True, text=True, check=False)
    lines = result.stdout.strip().split("\n")
    if len(lines) >= 2:  # Extract percentage and remove '%' character
        usage = lines[1].split()[4].replace("%", "")
        return int(usage)
    return 0


def create_large_file(filepath: Path, timeout: int = 5) -> None:
    """Create a large file using /dev/random with timeout."""
    with (
        contextlib.suppress(subprocess.TimeoutExpired),
        halo_progress(start_message="Creating file...", end_message="File created") as spinner,
    ):
        subprocess.run(
            ["dd", "if=/dev/random", f"of={filepath}", "bs=15m"],
            timeout=timeout,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        os.sync()  # Flush filesystem buffers
        spinner.text = "File created successfully"


def cleanup_files(directory: Path, error: bool = False) -> None:
    """Remove temporary files."""
    if directory.exists():
        try:
            shutil.rmtree(directory)
            if error:
                logger.warning("Operation incomplete. Cleaning up temp files.")
            else:
                logger.info("Temp files removed.")
        except Exception:
            logger.warning(
                "Failed to remove temporary files. Please remove %s manually.", directory
            )


def main() -> None:
    """Fill disk to force macOS to free purgeable space."""
    args = parse_args()

    min_free_space_gb = args.space
    min_free_space_bytes = min_free_space_gb * (1024 * 1024 * 1024)

    filesystem_path = Path(args.path)
    largefiles_dir = Path(args.directory)

    # Create the directory if it doesn't already exist
    largefiles_dir.mkdir(exist_ok=True, parents=True)

    # Get initial disk stats
    initial_free_space = get_free_space(filesystem_path)
    initial_percentage = get_disk_usage(filesystem_path)

    logger.info(
        "Initial disk state: %s%% full (%s free).",
        initial_percentage,
        format_space_in_gb(initial_free_space),
    )

    logger.info(
        "Filling until only %s free space remains.", format_space_in_gb(min_free_space_bytes)
    )

    # Main loop to fill the disk and track completion
    iteration = 1
    completed_normally = False

    # Define a keyboard interrupt handler for cleanup
    def interrupt_handler(signum: int = 0, frame: FrameType | None = None) -> None:  # noqa: ARG001
        cleanup_files(largefiles_dir, error=True)

    @handle_interrupt(callback=interrupt_handler, use_newline=True, logger=logger)
    def fill_disk() -> None:
        nonlocal iteration, completed_normally

        while True:
            # Check if we've reached our target
            current_free_space = get_free_space(filesystem_path)
            current_percentage = get_disk_usage(filesystem_path)

            # Stop condition
            if current_free_space <= min_free_space_bytes:
                logger.info(
                    "Target free space %s reached.", format_space_in_gb(min_free_space_bytes)
                )
                completed_normally = True
                break

            # Generate a large file
            filepath = largefiles_dir / f"largefile{iteration}"
            create_large_file(filepath)

            # Update usage stats
            current_free_space = get_free_space(filesystem_path)
            current_percentage = get_disk_usage(filesystem_path)

            logger.info(
                "File %s created, disk is now %s%% full (%s free)",
                iteration,
                current_percentage,
                format_space_in_gb(current_free_space),
            )
            iteration += 1

    # Run the filling process
    fill_disk()

    # Only proceed with final steps if we completed normally
    if completed_normally:
        # Clean up files
        cleanup_files(largefiles_dir)

        # Show final stats
        final_free_space = get_free_space(filesystem_path)
        final_percentage = get_disk_usage(filesystem_path)
        space_freed = final_free_space - initial_free_space

        if space_freed > 0:
            logger.info("Successfully freed %s of space!", format_space_in_gb(space_freed))

        logger.info(
            "All done! Disk is now %s%% full (%s free)",
            final_percentage,
            format_space_in_gb(final_free_space),
        )
