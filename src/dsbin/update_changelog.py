"""Update CHANGELOG.md with a new version and automatically manage links."""

from __future__ import annotations

import argparse
import re
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from logician import Logician

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = Logician.get_logger()

CHANGELOG_PATH = Path("CHANGELOG.md")
REPO_URL = "https://github.com/dannystewart/dsbin"


def get_latest_version() -> str:
    """Get the latest version from pyproject.toml.

    Raises:
        ValueError: If the version is not found in pyproject.toml.
    """
    try:
        with Path("pyproject.toml").open(encoding="utf-8") as f:
            for line in f:
                if match := re.search(r'version\s*=\s*["\']([^"\']+)["\']', line):
                    return match.group(1)
        msg = "Version not found in pyproject.toml"
        raise ValueError(msg)
    except Exception as e:
        logger.error("Failed to get version from pyproject.toml: %s", e)
        raise


def get_previous_version() -> str:
    """Get the previous version from the changelog."""
    try:
        content = CHANGELOG_PATH.read_text()
        # Look for the most recent version header
        if match := re.search(r"## \[(\d+\.\d+\.\d+)\]", content):
            return match.group(1)
        return "0.0.0"  # Fallback if no versions found
    except Exception as e:
        logger.error("Failed to get previous version from changelog: %s", e)
        return "0.0.0"


def create_version_entry(version: str, sections: dict[str, list[str]]) -> str:
    """Create a new version entry for the changelog."""
    today = time.strftime("%Y-%m-%d")
    entry = f"## [{version}] - {today}\n\n"

    for section, items in sections.items():
        if items:
            entry += f"### {section}\n"
            for item in items:
                entry += f"- {item}\n"
            entry += "\n"

    return entry


def create_new_changelog(version: str, new_entry: str) -> str:
    """Create a new changelog file with the given version entry."""
    return f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

{new_entry}
<!-- Links -->
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: {REPO_URL}/compare/v{version}...HEAD
[{version}]: {REPO_URL}/releases/tag/v{version}
"""


def insert_version_into_changelog(content: str, new_entry: str) -> str:
    """Insert a new version entry into an existing changelog."""
    match = re.search(r"## \[\d+\.\d+\.\d+\]", content)
    if not match:
        # No versions yet, insert after the intro
        parts = content.split("\n\n", 2)
        if len(parts) >= 2:
            return f"{parts[0]}\n\n{parts[1]}\n\n{new_entry}{parts[2] if len(parts) > 2 else ''}"
        return f"{content}\n\n{new_entry}"

    # Insert before the first version
    pos = match.start()
    return f"{content[:pos]}{new_entry}\n{content[pos:]}"


def update_version_links(content: str, version: str, prev_version: str) -> str:
    """Update the version links section in the changelog."""
    # Update unreleased link
    content = re.sub(
        r"\[unreleased\]: .*", f"[unreleased]: {REPO_URL}/compare/v{version}...HEAD", content
    )

    # Add new version link if it doesn't exist
    version_link_pattern = f"\\[{version}\\]: "
    if version_link_pattern not in content:
        if prev_version == "0.0.0":
            # First version
            version_link = f"[{version}]: {REPO_URL}/releases/tag/v{version}"
        else:
            # Compare with previous version
            version_link = f"[{version}]: {REPO_URL}/compare/v{prev_version}...v{version}"

        # Add the link in the right section
        if "<!-- Versions -->" in content:
            content = re.sub(
                r"(<!-- Versions -->.*?)(\n\n|$)",
                f"\\1\n{version_link}\\2",
                content,
                flags=re.DOTALL,
            )
        else:
            # Add Versions section if it doesn't exist
            content += f"\n<!-- Versions -->\n{version_link}\n"

    return content


def update_changelog(version: str, sections: dict[str, list[str]]) -> None:
    """Update the changelog with a new version entry and update all links."""
    try:
        new_entry = create_version_entry(version, sections)

        if not CHANGELOG_PATH.exists():
            # Create a new changelog if it doesn't exist
            content = create_new_changelog(version, new_entry)
            CHANGELOG_PATH.write_text(content)
            logger.info("Created new changelog with version %s.", version)
            return

        # Update existing changelog
        content = CHANGELOG_PATH.read_text()
        content = insert_version_into_changelog(content, new_entry)

        # Update version links
        prev_version = get_previous_version()
        content = update_version_links(content, version, prev_version)

        CHANGELOG_PATH.write_text(content)
        logger.info("Updated changelog with version %s", version)

    except Exception as e:
        logger.error("Failed to update changelog: %s", e)
        raise


def get_git_range(prev_version: str) -> str:
    """Determine the git range to examine based on previous version tag."""
    try:
        tag_prefix = "v"
        tag = f"{tag_prefix}{prev_version}"

        # Check if the tag exists
        result = subprocess.run(
            ["git", "tag", "-l", tag], capture_output=True, text=True, check=True
        )

        if tag not in result.stdout:
            logger.warning("Previous version tag %s not found, using all commits", tag)
            return ""
        return f"{tag}..HEAD"
    except subprocess.CalledProcessError as e:
        logger.error("Git command failed while determining range: %s", e)
        return ""


def fetch_commit_messages(git_range: str) -> list[str]:
    """Fetch commit messages for the specified git range."""
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%s", git_range],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        logger.error("Git command failed while fetching commits: %s", e)
        return []


def categorize_commits(commit_messages: list[str]) -> dict[str, list[str]]:
    """Categorize commit messages into changelog sections."""
    changes = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Removed": [],
        "Security": [],
        "Deprecated": [],
        "Updated": [],
    }

    for message in commit_messages:
        lower_message = message.lower()
        if any(word in lower_message for word in ["add", "new", "feature", "implement"]):
            changes["Added"].append(message)
        elif any(word in lower_message for word in ["fix", "bug", "issue", "error", "crash"]):
            changes["Fixed"].append(message)
        elif any(word in lower_message for word in ["remov", "delet"]):
            changes["Removed"].append(message)
        elif any(word in lower_message for word in ["secur", "vulnerab"]):
            changes["Security"].append(message)
        elif any(word in lower_message for word in ["deprecat"]):
            changes["Deprecated"].append(message)
        elif any(word in lower_message for word in ["updat", "bump", "upgrade"]):
            changes["Updated"].append(message)
        else:
            changes["Changed"].append(message)

    return {k: v for k, v in changes.items() if v}


def get_git_changes(prev_version: str) -> dict[str, list[str]]:
    """Get changes from git commits since the previous version."""
    try:
        git_range = get_git_range(prev_version)
        commit_messages = fetch_commit_messages(git_range)
        return categorize_commits(commit_messages)
    except Exception as e:
        logger.error("Failed to get git changes: %s", e)
        return {}


def edit_changelog() -> None:
    """Open the changelog in the default editor."""
    try:
        import os

        editor = os.environ.get("EDITOR", "vim")
        subprocess.run([editor, CHANGELOG_PATH], check=True)
    except Exception as e:
        logger.error("Failed to open editor: %s", e)


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update CHANGELOG.md with a new version")
    parser.add_argument(
        "--version", "-v", help="Version to add (defaults to version from pyproject.toml)"
    )
    parser.add_argument(
        "--auto",
        "-a",
        action="store_true",
        help="Automatically generate changelog entries from git commits",
    )
    parser.add_argument(
        "--no-edit",
        action="store_true",
        help="Don't open the changelog in an editor after updating",
    )
    return parser.parse_args(args)


def main() -> int:
    """Update the changelog with a new version."""
    args = parse_args()

    try:
        # Get the version to add
        version = args.version or get_latest_version()
        logger.info("Adding version %s to changelog.", version)

        # Get previous version
        prev_version = get_previous_version()

        # Get changes
        if args.auto:
            sections = get_git_changes(prev_version)
            if not sections:
                logger.warning("No changes found in git history, adding empty sections")
                sections = {"Added": [], "Changed": [], "Fixed": []}
        else:
            # Empty sections for manual editing
            sections = {"Added": [], "Changed": [], "Fixed": []}

        # Update the changelog
        update_changelog(version, sections)

        # Open in editor if requested
        if not args.no_edit:
            edit_changelog()

        return 0
    except Exception as e:
        logger.error("Failed to update changelog: %s", e)
        return 1


if __name__ == "__main__":
    main()
