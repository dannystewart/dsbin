#!/usr/bin/env python3

"""Tries to merge two folders, accounting for duplicates and name conflicts."""

from __future__ import annotations

import shutil
from pathlib import Path

from polykit import polykit_setup
from polykit.cli import confirm_action
from polykit.parsers import print_color as colored

from dsbin.files import FileManager

polykit_setup()


def merge_folders(first_folder: str, second_folder: str, dry_run: bool = False) -> None:
    """Merges two folders, accounting for duplicates and name conflicts.

    Args:
        first_folder: The path to the first folder.
        second_folder: The path to the second folder.
        dry_run: Whether to perform a dry run. Defaults to False.
    """
    files = FileManager()
    first_folder_path = Path(first_folder)
    second_folder_path = Path(second_folder)

    for second_file_path in second_folder_path.iterdir():
        if second_file_path.is_file():
            first_file_path = first_folder_path / second_file_path.name

            if first_file_path.exists():
                if files.sha256_checksum(first_file_path) == files.sha256_checksum(
                    second_file_path
                ):
                    print(f"Trashing duplicate: {second_file_path.name}")
                    if not dry_run:
                        second_file_path.unlink()
                else:
                    suffix = 1
                    new_name = f"{second_file_path.stem}_{suffix}{second_file_path.suffix}"
                    new_first_file_path = first_folder_path / new_name

                    while new_first_file_path.exists():
                        suffix += 1
                        new_name = f"{second_file_path.stem}_{suffix}{second_file_path.suffix}"
                        new_first_file_path = first_folder_path / new_name

                    print(f"Renaming and moving: {second_file_path.name} to {new_name}")
                    if not dry_run:
                        shutil.move(str(second_file_path), str(new_first_file_path))
            else:
                print(f"Moving: {second_file_path.name}")
                if not dry_run:
                    shutil.move(str(second_file_path), str(first_folder_path))


def main() -> None:
    """Main function."""
    first_folder = input("Enter the path to the first folder: ")
    second_folder = input("Enter the path to the second folder: ")

    if not Path(first_folder).is_dir() or not Path(second_folder).is_dir():
        print("One of the provided paths is not a directory!")
    else:
        print("Performing a dry run...")
        merge_folders(first_folder, second_folder, dry_run=True)

        if confirm_action("Do you want to proceed with the merge?"):
            merge_folders(first_folder, second_folder, dry_run=False)
            print(colored("Operation complete!", "green"))
        else:
            print(colored("Operation aborted.", "red"))


if __name__ == "__main__":
    main()
