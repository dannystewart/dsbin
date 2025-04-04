#!/usr/bin/env python3

"""Updates .python-version files recursively.

Finds .python-version files in the specified directory and its subdirectories and updates the Python
version in them after user confirmation. Allows customization of the directory and version numbers.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from polykit import polykit_setup
from polykit.cli import confirm_action
from polykit.shell import handle_interrupt
from walking_man import walking_man

polykit_setup()


@handle_interrupt()
def find_python_version_files(start_path: str) -> list[Path]:
    """Find .python-version files in the directory and its subdirectories.

    Args:
        start_path: Directory to start searching from.

    Returns:
        A list of file paths for .python-version files.
    """
    file_paths = []
    for root, _, files in os.walk(start_path):
        for file in files:
            if file == ".python-version":
                file_path = Path(root) / file
                file_paths.append(file_path)
    return file_paths


@handle_interrupt()
def update_python_version_file(file_path: str | Path, old_version: str, new_version: str) -> None:
    """Updates the Python version in the specified file.

    Args:
        file_path: Path to the .python-version file.
        old_version: The version string to be replaced.
        new_version: The version string to replace with.
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding="utf-8")

    if old_version in content:
        content = content.replace(old_version, new_version)
        file_path.write_text(content, encoding="utf-8")
        print(f"Updated {file_path}")


@handle_interrupt()
def main(start_path: str, old_version: str, new_version: str) -> None:
    """Recursively searches for .python-version files, lists them, and updates after confirmation.

    Args:
        start_path: Directory to start searching from.
        old_version: Old Python version to look for.
        new_version: New Python version to replace with.
    """
    with walking_man("Searching for .python-version files...", color="green"):
        file_paths = find_python_version_files(start_path)

    if not file_paths:
        print("No .python-version files found.")
        return

    print("Found .python-version files:")
    for file_path in file_paths:
        print(file_path)

    if confirm_action("Do you want to update these files?"):
        for file_path in file_paths:
            update_python_version_file(file_path, old_version, new_version)
    else:
        print("Update canceled.")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Update .python-version files recursively.")
    parser.add_argument(
        "--directory", default=Path.cwd(), help="Directory to start searching from."
    )
    parser.add_argument("--old-version", default="3.11.6", help="Old Python version to look for.")
    parser.add_argument(
        "--new-version", default="3.11.7", help="New Python version to replace with."
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    directory = args.directory
    old_ver = args.old_version
    new_ver = args.new_version

    main(directory, old_ver, new_ver)
