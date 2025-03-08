#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from dsutil import LocalLogger, configure_traceback
from dsutil.shell import handle_keyboard_interrupt

if TYPE_CHECKING:
    from types import FrameType

configure_traceback()

logger = LocalLogger().get_logger()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fill disk to a specified threshold")
    parser.add_argument(
        "-f", "--fill", type=int, default=98, help="desired fill percentage (default: 98)"
    )
    return parser.parse_args()


def get_disk_usage(path: str) -> int:
    """Get the current disk usage percentage for the specified path."""
    result = subprocess.run(["df", "-k", path], capture_output=True, text=True, check=False)
    lines = result.stdout.strip().split("\n")
    if len(lines) >= 2:  # Extract percentage and remove '%' character
        usage = lines[1].split()[4].replace("%", "")
        return int(usage)
    return 0


def create_large_file(filepath: Path, timeout: int = 5) -> None:
    """Create a large file using /dev/random with timeout."""
    with contextlib.suppress(subprocess.TimeoutExpired):
        subprocess.run(
            ["dd", "if=/dev/random", f"of={filepath}", "bs=15m"],
            timeout=timeout,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def cleanup_and_exit(signum: int = 0, frame: FrameType | None = None) -> None:  # noqa: ARG001
    """Handle Ctrl+C interrupt."""
    largefiles_dir = Path.home() / "largefiles"
    if largefiles_dir.exists():
        try:
            shutil.rmtree(largefiles_dir)
            return
        except Exception:
            return
    sys.exit(1)


@handle_keyboard_interrupt(callback=cleanup_and_exit, logger=logger)
def main() -> None:
    """Fill disk to the desired threshold."""
    args = parse_args()
    desired_threshold = args.fill

    # Get the appropriate path for disk usage check
    disk_path = "/System/Volumes/Data"

    # Get initial disk usage
    used_space = get_disk_usage(disk_path)

    # Create the directory if it doesn't already exist
    largefiles_dir = Path.home() / "largefiles"
    largefiles_dir.mkdir(exist_ok=True)

    logger.info("Disk is currently %s%% full (%s%% free).", used_space, 100 - used_space)
    logger.info("Filling until %s%% full (%s%% free).", desired_threshold, 100 - desired_threshold)

    # Main loop to fill the disk
    iteration = 1
    while used_space < desired_threshold:
        used_space = get_disk_usage(disk_path)

        # Generate a large file
        filepath = largefiles_dir / f"largefile{iteration}"
        create_large_file(filepath)

        logger.info(
            "File %s created, disk is now %s%% full (%s%% free).",
            iteration,
            used_space,
            100 - used_space,
        )
        iteration += 1

    # Cleanup
    if cleanup_and_exit():
        logger.info("Temporary files have been successfully removed.")
    else:
        logger.warning(
            "Failed to remove temporary files. Please remove ~/largefiles manually.",
        )

    # Final disk usage
    used_space = get_disk_usage(disk_path)
    logger.info("All done! Disk is now %s%% full (%s%% free).", used_space, 100 - used_space)
