#!/usr/bin/env python3

"""Replace an existing Git tag with a new tag name and description."""

from __future__ import annotations

import re
import subprocess
import sys

from polykit.cli import confirm_action
from polykit.parsers import print_color
from polykit.shell import handle_interrupt


def run_git_command(command: str | list[str]) -> str:
    """Run a Git command and return the output."""
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def check_if_tag_exists(tag: str) -> None:
    """Check if the tag exists in the Git repository."""
    try:
        run_git_command(["git", "show-ref", "--tags", tag])
    except subprocess.CalledProcessError:
        print_color(f"Tag '{tag}' does not exist.", "yellow")
        sys.exit(1)


def update_tag_in_repo(tag: str, new_tag: str, description: str) -> None:
    """Update an existing Git tag with a new tag name and description."""
    try:  # Delete existing tag
        run_git_command(["git", "tag", "-d", tag])
        print_color(f"Deleted local tag '{tag}'", "green")

        if description:  # Create new tag with description if provided
            run_git_command(["git", "tag", "-a", new_tag, "-m", description])
        else:
            run_git_command(["git", "tag", new_tag])

        print_color(f"Created tag '{new_tag}'", "green")
    except subprocess.CalledProcessError as e:
        print_color(f"Failed to update tag: {e}", "red")
        sys.exit(1)


@handle_interrupt()
def get_updated_name_and_description(tag: str, new_tag: str | None = None) -> tuple[str, str]:
    """Ask the user for the new tag name and description if not already provided."""
    if not new_tag:
        while True:
            new_tag = (
                input(f"Enter the new tag name for '{tag}' (press Enter to keep '{tag}'): ").strip()
                or tag
            )
            if validate_tag_name(new_tag):
                break
            print_color("Invalid characters in tag name. Please try again.", "red")

    description = input("Enter a tag description (press Enter to skip): ").strip()
    return new_tag, description


@handle_interrupt()
def push_tags_if_desired() -> None:
    """Push tags to remote if desired."""
    if confirm_action("Do you want to push the tags to remote?"):
        try:
            run_git_command(["git", "push", "origin", "--tags"])
            print_color("Tags pushed to remote.", "green")
        except subprocess.CalledProcessError as e:
            print_color(f"Failed to push tags: {e}", "red")
            sys.exit(1)
    else:
        print_color("Tags were not pushed to remote.", "green")


def validate_tag_name(tag: str) -> bool:
    """Validate the tag name by making sure it contains only valid characters."""
    return bool(re.match(r"^[\w.-]+$", tag))


@handle_interrupt()
def main() -> None:
    """Replace an existing Git tag with a new tag name and description."""
    tag = sys.argv[1].strip() if len(sys.argv) >= 2 else None
    new_tag = sys.argv[2].strip() if len(sys.argv) == 3 else None
    if not tag:
        print_color("Usage: tagreplace <tag_name> [new_tag_name]", "cyan")
        sys.exit(1)

    check_if_tag_exists(tag)
    if new_tag:
        description = input("Enter a tag description (press Enter to skip): ").strip()
    else:
        new_tag, description = get_updated_name_and_description(tag)
    update_tag_in_repo(tag, new_tag, description)
    push_tags_if_desired()


if __name__ == "__main__":
    main()
