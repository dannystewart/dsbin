#!/usr/bin/env python3

"""Build an rsync command interactively."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import inquirer
import pyperclip
from polykit import polykit_setup
from polykit.parsers import print_color
from polykit.shell import handle_interrupt

polykit_setup()


def get_full_path(path: Path, filename: Path) -> Path:
    """Return the full path of a file in a directory."""
    return Path(path) / filename


def get_first_item(path: Path) -> Path | None:
    """Return the first item in a directory."""
    try:
        for root, dirs, files in os.walk(path):
            if dirs:
                return Path(root) / dirs[0]
            if files:
                return Path(root) / files[0]
    except Exception:
        return None


@handle_interrupt()
def choose_operation() -> Path:
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


@handle_interrupt()
def get_paths() -> tuple[dict[str, Path] | None, bool]:
    """Get the source and destination paths."""
    questions = [
        inquirer.Text("source", message="Enter source path"),
        inquirer.Text("destination", message="Enter destination path"),
    ]
    paths = inquirer.prompt(questions)

    if paths is None:
        return None, False

    if not paths["source"] or not paths["destination"]:
        print_color("\nBoth source and destination paths are required.\n", "red")
        return paths, False

    source_path = Path(paths["source"]).expanduser().resolve()
    dest_path = Path(paths["destination"]).expanduser().resolve()

    if not source_path.exists():
        print_color(f"\nSource path does not exist: {source_path}", "red")
        return paths, False

    if not dest_path.exists():
        print_color(f"\nDestination path does not exist: {dest_path}", "red")
        return paths, False

    # Update paths with resolved paths
    paths["source"] = Path(source_path)
    paths["destination"] = Path(dest_path)

    return paths, True


@handle_interrupt()
def clarify_result(paths: dict[str, Path]) -> bool:
    """Clarify the result by showing the full path of the first item in the folder."""
    source = paths["source"]
    destination = paths["destination"]

    # Get the base name of the source
    source_base = source.name

    if first_item := get_first_item(source):
        if source.as_posix().endswith("/"):
            # If source ends with /, we're copying contents
            dest_path = destination / first_item.relative_to(source.parent / source.name)
        else:
            # Otherwise, we're copying the directory itself
            dest_path = destination / source_base / first_item.relative_to(source)

        print_color("In the source path, the first item is at:", "cyan")
        print_color(f" {first_item}", "yellow")
        print_color("In the destination path, it will be at:", "cyan")
        print_color(f" {dest_path}", "yellow")

        return inquirer.confirm("Is this correct?", default=True)

    print_color(
        "\nCouldn't find any items in the source folder. Please check the path and try again.",
        "red",
    )
    return False


@handle_interrupt()
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


def construct_command(base_command: Path, exclusions: list[str], paths: dict[str, str]) -> str:
    """Construct final command."""
    exclusions_str = " ".join(exclusions)
    return f"{base_command} {exclusions_str} '{paths['source']}' '{paths['destination']}'"


@handle_interrupt()
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

    print_color("\nYour rsync command:", "green")
    print_color(final_command, "cyan")

    pyperclip.copy(final_command)
    print_color("\nThe command has been copied to your clipboard.", "green")


if __name__ == "__main__":
    main()
