#!/usr/bin/env python3

"""Recursively moves nested DMG files to a desired location."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

from polykit import polykit_setup

polykit_setup()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Recursively moves nested DMG files to a desired location."
    )
    parser.add_argument(
        "final_path",
        metavar="final_path",
        type=str,
        help="The directory where DMG files will be moved.",
    )
    parser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove source files after moving (default is copy)",
    )
    return parser.parse_args()


def move_dmg_files(source_dir: str, dest_dir: str, remove_source_files: bool = False) -> None:
    """Recursively moves nested DMG files to a desired location.

    Args:
        source_dir: The source directory.
        dest_dir: The destination directory.
        remove_source_files: If True, remove the source files after moving.
    """
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(".dmg"):
                source_file_path = Path(root) / file
                relative_path = os.path.relpath(root, source_dir)
                destination_dir_path = Path(dest_dir) / relative_path
                Path(destination_dir_path).mkdir(parents=True, exist_ok=True)
                destination_file_path = Path(destination_dir_path) / file
                try:
                    if remove_source_files:
                        shutil.move(source_file_path, destination_file_path)
                    else:
                        shutil.copy2(source_file_path, destination_file_path)
                    print(f"Moved: {source_file_path} -> {destination_file_path}")
                except Exception as e:
                    print(f"Failed to move {source_file_path}: {e}")


def main() -> None:
    """Main function."""
    args = parse_arguments()
    try:
        move_dmg_files(".", args.final_path, args.remove)
        print("Operation completed successfully.")
    except Exception as e:
        print(f"An error occurred during the operation: {e}")


if __name__ == "__main__":
    main()
