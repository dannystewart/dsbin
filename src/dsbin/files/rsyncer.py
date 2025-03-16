#!/usr/bin/env python3

"""Build an rsync command interactively."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import inquirer
import pyperclip

from dsbase import configure_traceback
from dsbase.shell import handle_keyboard_interrupt
from dsbase.text import print_colored

configure_traceback()


def get_full_path(path: str, filename: str) -> str:
    """Return the full path of a file in a directory."""
    return os.path.join(path, filename)


def get_first_item(path: str) -> str | None:
    """Return the first item in a directory."""
    try:
        for root, dirs, files in os.walk(path):
            if dirs:
                return os.path.join(root, dirs[0])
            if files:
                return os.path.join(root, files[0])
    except Exception:
        return None


@handle_keyboard_interrupt()
def choose_operation() -> str:
    """Choose the command operation: copy, move, or synchronize."""
    questions = [
        inquirer.List(
            "operation",
            message="Choose operation",
            choices=[
                ("Copy", "rsync -avz --progress -h"),
                ("Move", "rsync -avz --progress -h --remove-source-files"),
                ("Synchronize", "rsync -avzu --delete --progress -h"),
            ],
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        sys.exit(1)
    return answers["operation"]


@handle_keyboard_interrupt()
def get_paths() -> tuple[dict[str, str] | None, bool]:
    """Get the source and destination paths."""
    questions = [
        inquirer.Text("source", message="Enter source path"),
        inquirer.Text("destination", message="Enter destination path"),
    ]
    paths = inquirer.prompt(questions)

    if paths is None:
        return None, False

    if not paths["source"] or not paths["destination"]:
        print_colored("\nBoth source and destination paths are required.\n", "red")
        return paths, False

    source_path = Path(paths["source"]).expanduser().resolve()
    dest_path = Path(paths["destination"]).expanduser().resolve()

    if not source_path.exists():
        print_colored(f"\nSource path does not exist: {source_path}", "red")
        return paths, False

    if not dest_path.exists():
        print_colored(f"\nDestination path does not exist: {dest_path}", "red")
        return paths, False

    # Update paths with resolved paths
    paths["source"] = str(source_path)
    paths["destination"] = str(dest_path)

    return paths, True


@handle_keyboard_interrupt()
def clarify_result(paths: dict) -> bool:
    """Clarify the result by showing the full path of the first item in the folder."""
    source = paths["source"]
    destination = paths["destination"]

    # Get the base name of the source
    source_base = os.path.basename(source.rstrip("/"))

    if first_item := get_first_item(source):
        source_base = os.path.basename(source.rstrip("/"))

        if source.endswith("/"):
            dest_path = os.path.join(destination, os.path.relpath(first_item, source.rstrip("/")))
        else:
            dest_path = os.path.join(destination, source_base, os.path.relpath(first_item, source))

        print_colored("In the source path, the first item is at:", "cyan")
        print_colored(f" {first_item}", "yellow")
        print_colored("In the destination path, it will be at:", "cyan")
        print_colored(f" {dest_path}", "yellow")

        return inquirer.confirm("Is this correct?", default=True)
    print_colored(
        "\nCouldn't find any items in the source folder. Please check the path and try again.",
        "red",
    )
    return False


@handle_keyboard_interrupt()
def check_exclusions(command: str) -> str:
    """Get any exclusions and whether exclusions should also be deleted."""
    exclusions = []
    while True:
        if exclusion := input("Enter an exclusion (or press Enter to finish): ").strip():
            exclusions.append(f"--exclude='{exclusion}'")
        else:
            break

    if exclusions:
        command += " " + " ".join(exclusions)
        if inquirer.confirm("Do you want to delete excluded files?", default=False):
            command += " --delete-excluded"

    return command


def construct_command(base_command: str, exclusions: list, paths: dict) -> str:
    """Construct final command."""
    exclusions_str = " ".join(exclusions)
    return f"{base_command} {exclusions_str} '{paths['source']}' '{paths['destination']}'"


@handle_keyboard_interrupt()
def main() -> None:
    """Build an rsync command interactively."""
    command = choose_operation()

    while True:
        paths, success = get_paths()
        if not success:
            if paths is None:
                return
            continue
        if clarify_result(paths):
            break

    command = check_exclusions(command)

    if paths:
        final_command = f"{command} '{paths['source']}' '{paths['destination']}'"

    print_colored("\nYour rsync command:", "green")
    print_colored(final_command, "cyan")

    pyperclip.copy(final_command)
    print_colored("\nThe command has been copied to your clipboard.", "green")


if __name__ == "__main__":
    main()
