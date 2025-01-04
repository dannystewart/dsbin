#!/usr/bin/env python3

"""Generate large files to fill the disk and free up purgeable space.

This script will create dummy files in a specified location until the free space available
on the drive is below a specified threshold, then delete the created files and check the
free space again. macOS is kind of stupid about freeing up large amounts of space, so this
script is a workaround to force it to clean up without having to reboot.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from dsutil import configure_traceback
from dsutil.progress import halo_progress
from dsutil.text import color as colored

configure_traceback()

# Sizes (in GB)
FILE_SIZE_IN_GB = 1  # Size of each file to be written (in GB)
MINIMUM_FREE_SPACE_IN_GB = 5  # Set a minimum threshold (in GB)


# You probably don't need to adjust these
PATH_TO_CREATE = "/tmp/large_file"  # Path to create the dummy file
FS_TO_CHECK = "/"  # Path to check the file system
GB_MULTIPLIER = 1024 * 1024 * 1024  # Multiplier to convert bytes to GB
FILE_SIZE = FILE_SIZE_IN_GB * GB_MULTIPLIER  # Size converted from bytes to GB
MINIMUM_FREE_SPACE = (
    MINIMUM_FREE_SPACE_IN_GB * GB_MULTIPLIER
)  # Minimum threshold converted from bytes to GB


def check_disk_usage(folder: str) -> int:
    """Return folder/drive free space (in bytes)."""
    _, _, free = shutil.disk_usage(folder)
    return free


def format_space(amount: int) -> str:
    """Helper function to convert bytes to GB and format the output."""
    factor = 1024 * 1024 * 1024
    return f"{amount / factor:.2f} GB"


def main():
    """Main function."""
    try:
        free_space_before = check_disk_usage(FS_TO_CHECK)
        print(f"Initial free space: {format_space(free_space_before)}")

        file_count = 0
        files_to_remove = []

        # While we have more free space than our minimum threshold, keep creating files
        while free_space_before > MINIMUM_FREE_SPACE + FILE_SIZE:
            # Create a uniquely named large file for each iteration
            filename = f"{PATH_TO_CREATE}_{file_count}.tmp"
            files_to_remove.append(filename)
            with halo_progress(
                start_message="Creating file...",
                end_message=f"File created (free space: {format_space(free_space_before)})",
            ) as spinner:
                # Create a large file with urandom for speed and non-redundancy
                with Path(filename).open("wb") as f:
                    f.write(os.urandom(FILE_SIZE))
                os.sync()  # Flush the filesystem buffers

                free_space_before = check_disk_usage(FS_TO_CHECK)
                spinner.text = f"File created. (Free space: {format_space(free_space_before)})"

                # If the free space is below the threshold, break
                if free_space_before <= MINIMUM_FREE_SPACE:
                    print(
                        colored(
                            f"Minimum free space reached: {format_space(free_space_before)}", "red"
                        )
                    )
                    break

            file_count += 1

        # Now delete all temporary files
        for filepath in files_to_remove:
            path = Path(filepath)
            if path.exists():
                path.unlink()
        print(colored("All temporary files removed.", "green"))

        # Check the final amount of free space
        free_space_after = check_disk_usage(FS_TO_CHECK)
        print(f"Free space after cleanup: {format_space(free_space_after)}")

    except KeyboardInterrupt:
        print(colored("Keyboard interrupt detected. Cleaning up temporary files...", "red"))

    except Exception as e:
        print(colored(f"An error occurred: {e}", "red"))

    finally:  # Always clean up, even if something goes wrong
        for filepath in files_to_remove:
            path = Path(filepath)
            if path.exists():
                path.unlink()
        print(colored("Temporary files cleaned up.", "red"))


if __name__ == "__main__":
    main()
