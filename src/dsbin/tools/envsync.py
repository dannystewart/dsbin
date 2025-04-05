#!/usr/bin/env python3

"""Synchronize two .env files by merging their content."""

from __future__ import annotations

import filecmp
from collections import OrderedDict
from pathlib import Path

from polykit.formatters import print_color

CHEZMOI_ENV = Path.home() / ".local" / "share" / "chezmoi" / "dot_local" / "bin" / ".env"
CHEZMOI_NAME = "Chezmoi .env"
HOME_ENV = Path.home() / ".local" / "bin" / ".env"
HOME_NAME = "Home .env"


def read_env_file(file_path: Path) -> OrderedDict[str, str]:
    """Read the content of a .env file and return it as an OrderedDict.

    Args:
        file_path: The path to the .env file to be read.

    Returns:
        An ordered dictionary containing the key-value pairs from the .env file.
    """
    env_dict = OrderedDict()
    with file_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()
    return env_dict


def write_env_file(file_path: Path, env_dict: OrderedDict[str, str]) -> None:
    """Write the content to a .env file.

    Args:
        file_path: The path to the .env file to be written.
        env_dict: An ordered dictionary containing the key-value pairs to be written.
    """
    with file_path.open("w", encoding="utf-8") as f:
        f.writelines(f"{key}={value}\n" for key, value in env_dict.items())


def sync_env_files(chezmoi_env: Path, home_env: Path) -> bool:
    """Synchronize two .env files by merging their content.

    This function reads two .env files, merges their contents, resolves conflicts if necessary, and
    writes the merged content back to both files.

    Args:
        chezmoi_env: The path to the first .env file (Chezmoi directory).
        home_env: The path to the second .env file (home directory).

    Returns:
        True if changes were made, False otherwise.
    """
    if filecmp.cmp(chezmoi_env, home_env):
        print_color("Files are already in sync. No changes made.", "green")
        return False

    env1 = read_env_file(chezmoi_env)
    env2 = read_env_file(home_env)

    # ...existing code...

    merged_env = OrderedDict()
    changes = []

    # Merge entries from both files
    all_keys = list(env1.keys()) + list(env2.keys())
    for key in OrderedDict.fromkeys(all_keys):  # Preserve order and remove duplicates
        if key in env1 and key in env2:
            if env1[key] != env2[key]:
                choice = input(
                    f"Conflict for {key}:\n1: {env1[key]} (from {CHEZMOI_NAME})"
                    f"\n2: {env2[key]} (from {HOME_NAME})\nChoose 1 or 2: "
                )
                merged_env[key] = env1[key] if choice == "1" else env2[key]
                changes.append(
                    f"Resolved conflict for '{key}': Chose '{merged_env[key]}' "
                    "from {CHEZMOI_NAME if choice == '1' else HOME_NAME}"
                )
            else:
                merged_env[key] = env1[key]
        elif key in env1:
            merged_env[key] = env1[key]
            changes.append(f"Added '{key}={env1[key]}' from {CHEZMOI_NAME} to {HOME_NAME}")
        else:
            merged_env[key] = env2[key]
            changes.append(f"Added '{key}={env2[key]}' from {HOME_NAME} to {CHEZMOI_NAME}")

    write_env_file(chezmoi_env, merged_env)
    write_env_file(home_env, merged_env)

    if changes:
        print_color("Files have been synchronized. Changes made:", "green")
        for change in changes:
            print_color(f"- {change}", "cyan")
    else:
        print_color("Files have been synchronized. No content changes were necessary.", "green")

    return bool(changes)


def main() -> None:
    """Run the sync_env_files function with the paths to the .env files.

    This function sets up the paths for the Chezmoi and Home .env files, calls the sync_env_files
    function, and handles potential exceptions.
    """
    try:
        sync_env_files(CHEZMOI_ENV, HOME_ENV)
    except FileNotFoundError as e:
        print_color(f"Error: {e}. Please check if the .env files exist.", "red")
    except PermissionError as e:
        print_color(f"Error: {e}. Please check file permissions.", "red")
    except Exception as e:
        print_color(f"An unexpected error occurred: {e}", "red")


if __name__ == "__main__":
    main()
