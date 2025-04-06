"""Create or update GitHub releases using content from CHANGELOG.md.

This script extracts version information from CHANGELOG.md and uses it to create or update GitHub
releases with the same content, ensuring consistency between your changelog and GitHub releases.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import PolyArgs
from polykit.log import PolyLog

if TYPE_CHECKING:
    import argparse

logger = PolyLog.get_logger()

CHANGELOG_PATH = Path("CHANGELOG.md")


def extract_version_content(version: str | None = None) -> tuple[str, str, str] | None:
    """Extract content for a specific version from CHANGELOG.md.

    Args:
        version: The version to extract. If None, extracts the latest version.

    Returns:
        A tuple of (version, date, content) if found, None otherwise.
    """
    if not CHANGELOG_PATH.exists():
        logger.error("CHANGELOG.md not found.")
        return None

    content = CHANGELOG_PATH.read_text(encoding="utf-8")

    # Find all version sections
    version_pattern = r"## \[(\d+\.\d+\.\d+)\](?: \((\d{4}-\d{2}-\d{2})\))?\n\n(.*?)(?=\n## |\Z)"
    matches = list(re.finditer(version_pattern, content, re.DOTALL))

    if not matches:
        logger.error("No version entries found in CHANGELOG.md.")
        return None

    if version is None:
        # Get the latest version (first match)
        match = matches[0]
        version_num = match.group(1)
        date = match.group(2) or "Unknown date"
        version_content = match.group(3).strip()
        return version_num, date, version_content

    # Find the requested version
    for match in matches:
        if match.group(1) == version:
            date = match.group(2) or "Unknown date"
            version_content = match.group(3).strip()
            return version, date, version_content

    logger.error("Version %s not found in CHANGELOG.md.", version)
    return None


def check_gh_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        # Check if gh is installed
        subprocess.run(["gh", "--version"], check=True, capture_output=True)

        # Check if authenticated
        result = subprocess.run(
            ["gh", "auth", "status"],
            check=False,  # Don't fail if not authenticated
            capture_output=True,
            text=True,
        )

        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_release_exists(tag: str) -> bool:
    """Check if a GitHub release with the given tag already exists.

    Args:
        tag: The tag to check for (e.g., 'v1.2.3').

    Returns:
        True if the release exists, False otherwise.
    """
    try:
        result = subprocess.run(["gh", "release", "view", tag], check=False, capture_output=True)
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


def create_or_update_release(version: str, content: str, dry_run: bool = False) -> bool:
    """Create or update a GitHub release with the provided content.

    Args:
        version: The version for the release (e.g., '1.2.3').
        content: The content for the release notes.
        dry_run: If True, print what would be done without executing.

    Returns:
        True if successful, False otherwise.
    """
    tag = f"v{version}"

    # Format content for GitHub release
    # Replace ### headers with bold text for better GitHub release formatting
    formatted_content = re.sub(r"### (.+)", r"**\1**", content)

    # Check if release exists first
    release_exists = check_release_exists(tag)

    if dry_run:
        action = "update" if release_exists else "create"
        logger.info("Would %s release %s with the following content:", action, tag)
        print("\n---\n" + formatted_content + "\n---\n")
        return True

    try:
        if release_exists:
            logger.info("Updating existing release %s.", tag)
            cmd = ["gh", "release", "edit", tag, "--notes", formatted_content]
        else:
            logger.info("Creating new release %s.", tag)
            cmd = ["gh", "release", "create", tag, "--notes", formatted_content]

        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Successfully %s release %s.", "updated" if release_exists else "created", tag)
        return True

    except subprocess.CalledProcessError as e:
        logger.error("Failed to %s release: %s", "update" if release_exists else "create", e.stderr)
        return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = PolyArgs(description=__doc__, add_version=False)
    parser.add_argument(
        "--version", "-v", help="Version to publish (defaults to latest version from CHANGELOG.md)"
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Print what would be done without creating/updating releases",
    )
    return parser.parse_args()


def main() -> int:
    """Extract changelog content and create/update GitHub release."""
    args = parse_args()

    if not check_gh_cli():
        logger.error(
            "GitHub CLI (gh) not found or not authenticated. "
            "Please install and authenticate with 'gh auth login'."
        )
        return 1

    # Extract content for the specified or latest version
    result = extract_version_content(args.version)
    if not result:
        return 1

    version, date, content = result

    logger.info("Found version %s (%s) in CHANGELOG.md.", version, date)

    # Create or update the GitHub release
    if create_or_update_release(version, content, args.dry_run):
        return 0
    return 1


if __name__ == "__main__":
    main()
