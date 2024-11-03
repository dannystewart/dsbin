#!/usr/bin/env python3

"""
Recursively moves nested DMG files to a desired location.
"""

import argparse
import os
import shutil


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Recursively moves nested DMG files to a desired location.")
    parser.add_argument(
        "final_path", metavar="final_path", type=str, help="The directory where DMG files will be moved."
    )
    parser.add_argument(
        "-r", "--remove", action="store_true", help="Remove source files after moving (default is copy)"
    )
    return parser.parse_args()


def move_dmg_files(source_dir, dest_dir, remove_source_files=False):
    """
    Recursively moves nested DMG files to a desired location.

    Args:
        source_dir (str): The source directory.
        dest_dir (str): The destination directory.
        remove_source_files (bool): If True, remove the source files after moving.
    """
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(".dmg"):
                source_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, source_dir)
                destination_dir_path = os.path.join(dest_dir, relative_path)
                os.makedirs(destination_dir_path, exist_ok=True)
                destination_file_path = os.path.join(destination_dir_path, file)
                try:
                    if remove_source_files:
                        shutil.move(source_file_path, destination_file_path)
                    else:
                        shutil.copy2(source_file_path, destination_file_path)
                    print(f"Moved: {source_file_path} -> {destination_file_path}")
                except Exception as e:
                    print(f"Failed to move {source_file_path}: {e}")


def main():
    """Main function."""
    args = parse_arguments()
    try:
        move_dmg_files(".", args.final_path, args.remove)
        print("Operation completed successfully.")
    except Exception as e:
        print(f"An error occurred during the operation: {e}")


if __name__ == "__main__":
    main()
