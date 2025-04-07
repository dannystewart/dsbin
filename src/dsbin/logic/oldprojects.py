#!/usr/bin/env python3

"""Moves old Logic projects out of folders then deletes empty folders.

Logic's "Save a Copy" behavior used to save a copy of the project file by itself rather
than repackaging all its related files into a folder like a regular save, but a recent
version changed this behavior to match what a regular save does. I use "Save a Copy" as a
way of saving backup projects to copy things from later and I liked the old behavior, so
this script moves the project files up a level and deletes the empty folders so I only
keep the project files, like the old behavior used to do.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import colorama
import readchar
from colorama import Fore, Style
from polykit.core import platform_check, polykit_setup

polykit_setup()

# Check if the script is running on macOS
platform_check()


@dataclass
class Operations:
    """A set of operations to be performed."""

    move: list[tuple[Path, Path]]
    delete: list[Path]


def format_path(path: str, base_dir: str) -> str:
    """Format a path to be relative to the base directory."""
    return path.replace(base_dir + os.sep, "")


def confirm_actions(operations: Operations, base_dir: str) -> bool:
    """Confirm the actions to be performed."""
    print(f"{Fore.YELLOW}Project files that will be moved:{Style.RESET_ALL}")
    for _, dest in operations.move:
        print(f"{Fore.YELLOW}→ {Style.RESET_ALL}{format_path(str(dest), base_dir)}")

    print("\n" + Fore.RED + "Folders that will be deleted:" + Style.RESET_ALL)
    for delete in operations.delete:
        print(f"{Fore.RED}✖ {Style.RESET_ALL}{format_path(str(delete), base_dir)}")

    print("\nDo you want to proceed? (y/n) ", end="")
    key = readchar.readkey()
    print()
    return key.lower() == "y"


def perform_operations(operations: Operations, base_dir: str) -> None:
    """Perform the specified operations."""
    for src, dest in operations.move:
        shutil.move(src, dest)
        print(f"{Fore.GREEN}✔ Moved {Style.RESET_ALL}{format_path(str(dest), base_dir)}")

    for del_path in operations.delete:
        subprocess.run(["trash", del_path], check=False)
        print(f"{Fore.RED}✔ Deleted {Style.RESET_ALL}{format_path(str(del_path), base_dir)}")


def move_and_delete_logic_folders() -> None:
    """Move the Logic projects up from their folders and then delete empty folders."""
    colorama.init()
    base_dir = Path(Path.cwd())
    operations = Operations(move=[], delete=[])

    print("Searching in:", base_dir.name)

    try:
        for root, dirs, _ in os.walk(base_dir):
            if Path(root).name == "Old Projects":
                for subdir in dirs:
                    subdir_path = Path(root) / subdir
                    logicx_folders = [f for f in subdir_path.glob("*.logicx") if f.is_dir()]
                    for logicx_path in logicx_folders:
                        new_location = Path(root) / logicx_path.name
                        operations.move.append((logicx_path, new_location))
                        operations.delete.append(subdir_path)

        if operations.move or operations.delete:
            if confirm_actions(operations, str(base_dir)):
                perform_operations(operations, str(base_dir))
                print(Fore.GREEN + "\nOperations completed." + Style.RESET_ALL)
            else:
                print(Fore.RED + "\nOperation aborted." + Style.RESET_ALL)
        else:
            print(Fore.RED + "\nNo .logicx folders found for moving." + Style.RESET_ALL)
    except Exception as e:
        print(f"{Fore.RED}\nAn error occurred: {e!s}{Style.RESET_ALL}")


if __name__ == "__main__":
    move_and_delete_logic_folders()
