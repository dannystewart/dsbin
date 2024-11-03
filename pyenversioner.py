#!/usr/bin/env python3

"""
Updates .python-version files recursively.

Finds .python-version files in the specified directory and its subdirectories and
updates the Python version in them after user confirmation. Allows customization of the directory and version numbers.
"""

import argparse
import os

from dsutil import animation
from dsutil.shell import confirm_action, handle_keyboard_interrupt
from termcolor import colored


@handle_keyboard_interrupt()
def find_python_version_files(start_path):
    """
    Find .python-version files in the directory and its subdirectories.

    Args:
        start_path (str): Directory to start searching from.

    Returns:
        List[str]: A list of file paths for .python-version files.
    """
    file_paths = []
    for root, _, files in os.walk(start_path):
        for file in files:
            if file == ".python-version":
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
    return file_paths


@handle_keyboard_interrupt()
def update_python_version_file(file_path, old_version, new_version):
    """
    Updates the Python version in the specified file.

    Args:
        file_path (str): Path to the .python-version file.
        old_version (str): The version string to be replaced.
        new_version (str): The version string to replace with.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    if old_version in content:
        content = content.replace(old_version, new_version)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Updated {file_path}")


@handle_keyboard_interrupt()
def main(start_path, old_version, new_version):
    """
    Recursively searches for .python-version files, lists them, and updates after confirmation.

    Args:
        start_path (str): Directory to start searching from.
        old_version (str): Old Python version to look for.
        new_version (str): New Python version to replace with.
    """
    print(colored("Searching for .python-version files...", "green"))

    animation_thread = animation.start_animation()
    file_paths = find_python_version_files(start_path)
    animation.stop_animation(animation_thread)

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
        print("Update cancelled.")


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Update .python-version files recursively.")
    parser.add_argument("--directory", default=os.getcwd(), help="Directory to start searching from.")
    parser.add_argument("--old-version", default="3.11.6", help="Old Python version to look for.")
    parser.add_argument("--new-version", default="3.11.7", help="New Python version to replace with.")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    directory = args.directory
    old_ver = args.old_version
    new_ver = args.new_version

    main(directory, old_ver, new_ver)
