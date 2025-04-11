"""Update CHANGELOG.md with a new version and automatically manage links."""

from __future__ import annotations

import re
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import PolyArgs
from polykit.log import PolyLog

if TYPE_CHECKING:
    import argparse
    from collections.abc import Sequence

logger = PolyLog.get_logger()

CHANGELOG_PATH = Path("CHANGELOG.md")


def get_repo_url(repo_override: str | None = None) -> str:
    """Get the GitHub repository URL."""
    if repo_override:
        return f"https://github.com/dannystewart/{repo_override}"

    # Try to get repo name from git remote
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()

        # Extract repo name from URL
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        if parsed_url.hostname == "github.com":
            if url.startswith("git@github.com:"):
                # SSH format: git@github.com:username/repo.git
                repo_name = url.split(":")[-1].split("/")[-1].rstrip(".git")
            else:
                # HTTPS format: https://github.com/username/repo.git
                repo_name = url.split("/")[-1].rstrip(".git")

            return f"https://github.com/dannystewart/{repo_name}"
    except subprocess.CalledProcessError:
        logger.warning("Failed to get git remote URL, falling back to directory name.")

    # Fallback to directory name
    repo_name = Path.cwd().name
    return f"https://github.com/dannystewart/{repo_name}"


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
        logger.error("Failed to get version from pyproject.toml: %s", str(e))
        raise


def get_previous_version() -> str:
    """Get the previous version from the changelog."""
    try:
        content = CHANGELOG_PATH.read_text()
        # Look for all version headers
        versions = re.findall(r"## \[(\d+\.\d+\.\d+)\]", content)

        if not versions:
            logger.debug("No versions found in changelog.")
            return "0.0.0"  # Fallback if no versions found

        logger.debug("Found versions in changelog: %s", versions)
        return versions[0]  # Return the most recent version
    except Exception as e:
        logger.debug("Error reading changelog: %s", str(e))
        return "0.0.0"


def create_version_entry(version: str, sections: dict[str, list[str]]) -> str:
    """Create a new version entry for the changelog."""
    today = time.strftime("%Y-%m-%d")
    entry = f"## [{version}] ({today})\n\n"

    for section, items in sections.items():
        if items:
            entry += f"### {section}\n"
            for item in items:
                entry += f"- {item}\n"
            entry += "\n"

    return entry


def create_new_changelog(version: str, new_entry: str, repo_url: str) -> str:
    """Create a new changelog file with the given version entry."""
    return f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog], and this project adheres to [Semantic Versioning].

## [Unreleased]

{new_entry}
<!-- Links -->
[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: {repo_url}/compare/v{version}...HEAD
[{version}]: {repo_url}/releases/tag/v{version}
"""


def insert_version_into_changelog(content: str, new_entry: str, version: str) -> str:
    """Insert a new version entry into an existing changelog, maintaining version order."""
    from packaging import version as pkg_version

    # Find the Unreleased section
    unreleased_match = re.search(r"## \[Unreleased\].*?\n(?:\n|$)", content, re.IGNORECASE)

    # When adding a new version, check if there's content in the Unreleased section
    # If there is, insert the new version entry right after the Unreleased header
    if unreleased_match:
        unreleased_content_match = re.search(
            r"## \[Unreleased\].*?\n\n(.*?)(?=\n## |\Z)", content, re.DOTALL
        )
        if unreleased_content_match and unreleased_content_match.group(1).strip():
            # There's content in the Unreleased section, insert after the header
            pos = unreleased_match.end()
            return f"{content[:pos]}{new_entry}{content[pos:]}"

    # If no Unreleased section with content, proceed with normal version ordering
    # Extract all existing version headers
    version_matches = list(re.finditer(r"## \[(\d+\.\d+\.\d+)\]", content))
    existing_versions = [(m.group(1), m.start()) for m in version_matches]

    # If no versions exist yet
    if not existing_versions:
        if unreleased_match:
            # Insert after the Unreleased section
            pos = unreleased_match.end()
            return f"{content[:pos]}{new_entry}{content[pos:]}"

        # No Unreleased section either, insert at the beginning or after intro
        parts = content.split("\n\n", 2)
        if len(parts) >= 2:
            return f"{parts[0]}\n\n{parts[1]}\n\n{new_entry}{parts[2] if len(parts) > 2 else ''}"
        return f"{content}\n\n{new_entry}"

    # Sort existing versions
    version_obj = pkg_version.parse(version)

    # Find the position to insert the new version
    insert_pos = None

    for existing_ver, pos in existing_versions:
        existing_ver_obj = pkg_version.parse(existing_ver)
        if version_obj > existing_ver_obj:
            insert_pos = pos
            break

    if insert_pos is not None:
        # Insert before the first version that's smaller than the new version
        return f"{content[:insert_pos]}{new_entry}{content[insert_pos:]}"

    # If the new version is smaller than all existing versions, add it at the end
    # Find the end of the last version section
    last_version_pos = existing_versions[-1][1]

    # Find the next section after the last version (if any)
    next_section_match = re.search(r"^#", content[last_version_pos:], re.MULTILINE)
    if next_section_match:
        insert_pos = last_version_pos + next_section_match.start()
    else:
        # No next section, insert at the end or before the links section
        links_section = re.search(r"<!-- Links -->", content)
        insert_pos = links_section.start() if links_section else len(content)

    return f"{content[:insert_pos]}{new_entry}{content[insert_pos:]}"


def update_version_links(content: str, version: str, repo_url: str) -> str:
    """Update the version links section in the changelog."""
    from packaging import version as pkg_version

    # Extract all existing version links
    links = {}
    for match in re.finditer(r"\[([\d\.]+)\]: (.*)", content):
        ver, url = match.groups()
        links[ver] = url

    # Add the new version if it doesn't exist
    if version not in links:
        # Default link will be updated later
        links[version] = ""

    # Get all versions and sort them
    versions = [v for v in links if v != "unreleased"]
    versions_sorted = sorted(versions, key=pkg_version.parse, reverse=True)

    # Regenerate comparison links for all versions to ensure consistency
    for i, ver in enumerate(versions_sorted):
        # Skip the last version as it has no previous version to compare with
        if i == len(versions_sorted) - 1:
            # For the oldest version, use the release tag URL
            links[ver] = f"{repo_url}/releases/tag/v{ver}"
            continue

        next_ver = versions_sorted[i + 1]

        # Only regenerate URLs that follow the standard comparison pattern
        # This preserves any custom URLs that don't match the pattern
        current_url = links[ver]
        standard_pattern = f"{repo_url}/compare/v"

        # If URL doesn't exist or matches standard pattern, regenerate it
        if not current_url or current_url.startswith(standard_pattern):
            links[ver] = f"{repo_url}/compare/v{next_ver}...v{ver}"

    # Update unreleased link to point to the highest version
    if versions_sorted:
        highest_version = versions_sorted[0]
        links["unreleased"] = f"{repo_url}/compare/v{highest_version}...HEAD"
    else:
        links["unreleased"] = f"{repo_url}/compare/main...HEAD"

    # Build the new versions section
    new_links_section = "<!-- Versions -->\n"
    new_links_section += f"[unreleased]: {links['unreleased']}\n"
    for ver in versions_sorted:
        new_links_section += f"[{ver}]: {links[ver]}\n"

    # Replace the entire versions section
    if "<!-- Versions -->" in content:
        content = re.sub(
            r"<!-- Versions -->.*?(\n\n|$)",
            new_links_section + "\n",
            content,
            flags=re.DOTALL,
        )
    else:
        # Add Versions section if it doesn't exist
        content += f"\n{new_links_section}\n"

    return content


def update_changelog(version: str, sections: dict[str, list[str]], repo_url: str) -> bool:
    """Update the changelog with a new version entry and update all links."""
    try:
        new_entry = create_version_entry(version, sections)

        if not CHANGELOG_PATH.exists():
            # Create a new changelog if it doesn't exist
            content = create_new_changelog(version, new_entry, repo_url)
            CHANGELOG_PATH.write_text(content)
            logger.info("Created new changelog with version %s.", version)
            return True

        # Update existing changelog
        content = CHANGELOG_PATH.read_text()

        # Check if version already exists
        if re.search(rf"## \[{re.escape(version)}\]", content):
            logger.info("Version %s already exists in changelog, skipping entry creation.", version)
            section_exists = True
        else:
            logger.info("Adding version %s to changelog.", version)
            content = insert_version_into_changelog(content, new_entry, version)
            section_exists = False

        # Update version links
        content = update_version_links(content, version, repo_url)

        # Ensure exactly one blank line at the end of the file
        content = content.rstrip("\n") + "\n"

        CHANGELOG_PATH.write_text(content)

        if not section_exists:
            logger.info("Updated changelog with version %s.", version)

        return not section_exists  # Indicate whether the editor should be opened

    except Exception as e:
        logger.error("Failed to update changelog: %s", str(e))
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
            logger.warning("Previous version tag %s not found, using all commits.", tag)
            return ""
        return f"{tag}..HEAD"
    except subprocess.CalledProcessError as e:
        logger.error("Git command failed while determining range: %s", str(e))
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
        logger.error("Git command failed while fetching commits: %s", str(e))
        return []


def categorize_commits(commit_messages: list[str]) -> dict[str, list[str]]:
    """Categorize commit messages into changelog sections based on conventional commits."""
    changes = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Removed": [],
        "Security": [],
        "Deprecated": [],
        "Updated": [],
    }

    type_to_section = {
        "feat": "Added",
        "fix": "Fixed",
        "perf": "Changed",
        "refactor": "Changed",
        "docs": "Updated",
    }

    for message in commit_messages:
        match = re.match(r"^(\w+)(?:\(([^)]+)\))?: (.+)$", message)
        if match:
            type_, scope, desc = match.groups()
            section = type_to_section.get(type_, "Changed")
            prefix = f"**{scope}**: " if scope else ""
            changes[section].append(f"{prefix}{desc}")
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
        logger.error("Failed to get Git changes: %s", str(e))
        return {}


def edit_changelog() -> None:
    """Open the changelog in the default editor. Tries VS Code first, then nano."""
    try:
        import os
        import shutil

        if shutil.which("code"):  # Check if VS Code is available
            logger.debug("Opening changelog with VS Code.")
            subprocess.run(["code", CHANGELOG_PATH], check=True)
        else:  # Fall back to $EDITOR or nano
            editor = os.environ.get("EDITOR", "nano")
            logger.debug("VS Code not found, opening changelog with %s.", editor)
            subprocess.run([editor, CHANGELOG_PATH], check=True)
    except Exception as e:
        logger.warning("Couldn't open editor: %s", str(e))


def find_previous_version(version: str) -> str:
    """Find the previous version in the changelog.

    Args:
        version: The current version.

    Returns:
        The previous version, or "0.0.0" if none found.
    """
    try:
        changelog_content = CHANGELOG_PATH.read_text()
        versions = re.findall(r"## \[(\d+\.\d+\.\d+)\]", changelog_content)

        if len(versions) > 1:
            # Find the version that comes after the current one in the list
            for i, ver in enumerate(versions):
                if ver == version and i + 1 < len(versions):
                    prev_version = versions[i + 1]
                    logger.debug("Found previous version: %s (current: %s).", prev_version, version)
                    return prev_version

        logger.debug("No previous version found for %s.", version)
        return "0.0.0"
    except Exception as e:
        logger.error("Error finding previous version: %s", str(e))
        return "0.0.0"


def extract_version_content(version: str) -> str | None:
    """Extract the content for a specific version from the changelog.

    Args:
        version: The version to extract content for.

    Returns:
        The extracted content, or None if not found.
    """
    try:
        content = CHANGELOG_PATH.read_text()
        version_pattern = rf"## \[{re.escape(version)}\].*?\n\n(.*?)(?=\n## |\Z)"
        match = re.search(version_pattern, content, re.DOTALL)

        if not match:
            logger.error("Failed to extract content for version %s from changelog.", version)
            return None

        return match.group(1).strip()
    except Exception as e:
        logger.error("Failed to extract version content: %s", str(e))
        return None


def add_or_update_changelog_link(
    content: str, version: str, prev_version: str, repo_url: str
) -> str:
    """Add or update the Full Changelog link in the content.

    Args:
        content: The release notes content.
        version: The current version.
        prev_version: The previous version.
        repo_url: The repository URL.

    Returns:
        The content with the changelog link added or updated.
    """
    # Check if we have a valid previous version
    if prev_version == "0.0.0":
        logger.debug("Skipping changelog link: no previous version found.")
        return content

    # Prepare the changelog link
    changelog_link = f"**Full Changelog:** {repo_url}/compare/v{prev_version}...v{version}"

    # Check if the content already has a Full Changelog link
    if "Full Changelog:" not in content:
        # Add the link with proper spacing
        if not content.endswith("\n\n"):
            if content.endswith("\n"):
                content += "\n"
            else:
                content += "\n\n"

        logger.debug("Adding changelog link: %s", changelog_link)
        return content + changelog_link
    # Update the existing link
    updated_content = re.sub(
        r"(?:\*\*)?Full Changelog:(?:\*\*)? .*",
        changelog_link,
        content,
    )
    logger.debug("Updated existing changelog link.")
    return updated_content


def check_release_exists(tag: str) -> bool:
    """Check if a GitHub release with the given tag exists.

    Args:
        tag: The tag to check.

    Returns:
        True if the release exists, False otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag], check=False, capture_output=True, text=True
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        logger.error("Failed to check if release exists.")
        return False


def execute_gh_command(cmd: list[str]) -> bool:
    """Execute a GitHub CLI command."""
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("GitHub CLI command failed: %s", e.stderr)
        return False


def get_changelog_versions() -> list[tuple[str, str]]:
    """Extract all versions and their content from the changelog.

    Returns:
        List of (version, content) tuples.
    """
    if not CHANGELOG_PATH.exists():
        logger.error("Changelog file not found.")
        return []

    try:
        changelog_content = CHANGELOG_PATH.read_text()

        # Extract all versions from the changelog
        version_pattern = r"## \[(\d+\.\d+\.\d+)\].*?\n\n(.*?)(?=\n## |\Z)"
        version_matches = re.finditer(version_pattern, changelog_content, re.DOTALL)

        versions = []
        for match in version_matches:
            version = match.group(1)
            content = match.group(2).strip()
            versions.append((version, content))

        logger.info("Found %d versions in changelog.", len(versions))
        return versions
    except Exception as e:
        logger.error("Failed to extract versions from changelog: %s", str(e))
        return []


def get_release_notes(tag: str) -> str | None:
    """Get the release notes for a GitHub release.

    Args:
        tag: The release tag.

    Returns:
        The release notes, or None if the release doesn't exist or an error occurred.
    """
    try:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--json", "body"],
            capture_output=True,
            text=True,
            check=True,
        )
        import json

        release_data = json.loads(result.stdout)
        return release_data.get("body", "")
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logger.error("Failed to get release notes for %s: %s", tag, str(e))
        return None


def update_single_release(
    version: str, content: str, repo_url: str, dry_run: bool = False, open_url: bool = False
) -> bool:
    """Check and update a single GitHub release.

    Args:
        version: The version number.
        content: The changelog content for this version.
        repo_url: The repository URL.
        dry_run: If True, only report issues without making changes.
        open_url: If True, open the release URL in the browser after updating.

    Returns:
        True if the release was updated or is up to date, False on error.
    """
    tag = f"v{version}"

    # Check if release exists
    if not check_release_exists(tag):
        logger.info("GitHub release %s does not exist, skipping.", tag)
        return False

    # Get current release notes
    current_notes = get_release_notes(tag)
    if current_notes is None:
        return False

    # Find the previous version for the changelog link
    prev_version = find_previous_version(version)

    # Format the changelog content with the link
    formatted_content = add_or_update_changelog_link(content, version, prev_version, repo_url)

    # Compare and update if different
    if current_notes.strip() != formatted_content.strip():
        logger.info("GitHub release %s needs updating.", tag)

        if dry_run:
            return True

        cmd = ["gh", "release", "edit", tag, "--notes", formatted_content]
        if execute_gh_command(cmd):
            logger.info("Successfully updated GitHub release %s.", tag)

            if open_url:
                open_release_url(repo_url, version)
            return True
        logger.error("Failed to update GitHub release %s.", tag)
        return False
    logger.info("GitHub release %s is up to date.", tag)
    return True


def check_and_update_release(
    version: str, content: str, repo_url: str, dry_run: bool, open_url: bool
) -> tuple[bool, bool]:
    """Check if a release needs updating and update it if needed.

    Args:
        version: The version number.
        content: The changelog content.
        repo_url: The repository URL.
        dry_run: If True, don't actually update.
        open_url: If True, open the URL after updating.

    Returns:
        Tuple of (needs_update, was_updated).
    """
    tag = f"v{version}"

    # Check if release exists
    if not check_release_exists(tag):
        logger.info("GitHub release %s does not exist, skipping.", tag)
        return False, False

    # Get current release notes
    current_notes = get_release_notes(tag)
    if current_notes is None:
        return False, False

    # Find the previous version for the changelog link
    prev_version = find_previous_version(version)

    # Format the changelog content with the link
    formatted_content = add_or_update_changelog_link(content, version, prev_version, repo_url)

    # Compare and see if update is needed
    needs_update = current_notes.strip() != formatted_content.strip()
    was_updated = False

    if needs_update:
        logger.info("GitHub release %s needs updating.", tag)

        if not dry_run:
            cmd = ["gh", "release", "edit", tag, "--notes", formatted_content]
            if execute_gh_command(cmd):
                was_updated = True
                logger.info("Successfully updated GitHub release %s.", tag)

                if open_url:
                    open_release_url(repo_url, version)
            else:
                logger.error("Failed to update GitHub release %s.", tag)
    else:
        logger.info("GitHub release %s is up to date.", tag)

    return needs_update, was_updated


def sync_github_releases(repo_url: str, dry_run: bool = False, open_url: bool = False) -> int:
    """Verify and sync all GitHub releases with changelog content.

    Args:
        repo_url: The repository URL.
        dry_run: If True, only report issues without making changes.
        open_url: If True, open updated release URLs in the browser.

    Returns:
        Number of releases that were updated.
    """
    # Get all versions from the changelog
    versions = get_changelog_versions()
    if not versions:
        return 0

    # Track updates
    updates_needed = 0
    updates_made = 0

    # Process each version
    for version, content in versions:
        needs_update, was_updated = check_and_update_release(
            version, content, repo_url, dry_run, open_url
        )

        if needs_update:
            updates_needed += 1

        if was_updated:
            updates_made += 1

    # Report results
    if dry_run and updates_needed > 0:
        logger.info(
            "%d GitHub releases need updating. Run without --dry-run to apply changes.",
            updates_needed,
        )
    elif updates_needed == 0:
        logger.info("All GitHub releases are up to date with the changelog.")
    else:
        logger.info("Updated %d GitHub releases to match the changelog.", updates_made)

    return updates_made


def update_github_release(
    version: str, content: str, repo_url: str, dry_run: bool = False, open_url: bool = True
) -> bool:
    """Update a GitHub release with content from the changelog.

    Args:
        version: The version for the release (e.g., '1.2.3')
        content: The content for the release notes.
        repo_url: The GitHub repository URL.
        dry_run: If True, print what would be done without executing.
        open_url: If True, open the release URL in a browser after updating.

    Returns:
        True if successful, False otherwise.
    """
    tag = f"v{version}"

    # Find the previous version
    prev_version = find_previous_version(version)

    # Add or update the changelog link
    formatted_content = add_or_update_changelog_link(content, version, prev_version, repo_url)

    # Check if release exists
    release_exists = check_release_exists(tag)

    if not release_exists:
        logger.error(
            "GitHub release %s does not exist. Please create the release on GitHub first.", tag
        )
        return False

    if dry_run:
        logger.info("Would update GitHub release %s with the following content:", tag)
        print("\n" + formatted_content)
        return True

    # Update the release
    logger.info("Updating GitHub release %s.", tag)
    cmd = ["gh", "release", "edit", tag, "--notes", formatted_content]

    success = execute_gh_command(cmd)

    if success:
        logger.info("Successfully updated GitHub release %s.", tag)

        # Open the release URL in the browser if requested
        if open_url:
            open_release_url(repo_url, version)

    return success


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


def open_release_url(repo_url: str, version: str) -> None:
    """Open the GitHub release URL in the default browser.

    Args:
        repo_url: The repository URL.
        version: The version number.
    """
    release_url = f"{repo_url}/releases/tag/v{version}"
    try:
        logger.info("Opening release URL: %s", release_url)
        webbrowser.open(release_url)
    except Exception as e:
        logger.error("Failed to open release URL: %s", str(e))


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = PolyArgs(description=__doc__)
    parser.add_argument(
        "--version", "-v", help="version to add (defaults to version from pyproject.toml)"
    )
    parser.add_argument(
        "--auto",
        "-a",
        action="store_true",
        help="automatically generate changelog entries from git commits",
    )
    parser.add_argument(
        "--no-edit",
        action="store_true",
        help="don't open the changelog in an editor after updating",
    )
    parser.add_argument(
        "--repo", "-r", help="repository name to use for links (defaults to auto-detection)"
    )
    parser.add_argument(
        "--github-release",
        "-g",
        action="store_true",
        help="update an existing GitHub release with the changelog content",
    )
    parser.add_argument(
        "--sync-releases",
        "-s",
        action="store_true",
        help="check all GitHub releases against changelog entries and update if needed",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be done without making any changes",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="open the GitHub release URL after updating",
    )
    return parser.parse_args(args)


def main() -> int:
    """Update the changelog with a new version."""
    args = parse_args()

    try:
        # Get repo URL
        repo_url = get_repo_url(args.repo)

        # Check if we're in sync mode
        if args.sync_releases:
            if not check_gh_cli():
                logger.error(
                    "GitHub CLI (gh) not found or not authenticated. "
                    "Please install and authenticate with 'gh auth login'."
                )
                return 1

            sync_github_releases(repo_url, dry_run=args.dry_run, open_url=args.open)
            return 0

        # Get the version to add
        version = args.version or get_latest_version()

        # Get previous version
        prev_version = get_previous_version()

        # Get changes
        if args.auto:
            sections = get_git_changes(prev_version)
            if not sections:
                logger.warning("No changes found in git history, adding empty sections.")
                sections = {"Added": [], "Changed": [], "Fixed": []}
        else:
            # Empty sections for manual editing
            sections = {"Added": [], "Changed": [], "Fixed": []}

        # Update the changelog
        requires_edit = update_changelog(version, sections, repo_url)

        # Open in editor if requested
        if not args.no_edit and requires_edit:
            edit_changelog()

        # Update GitHub release if requested
        if args.github_release:
            if not check_gh_cli():
                logger.error(
                    "GitHub CLI (gh) not found or not authenticated. "
                    "Please install and authenticate with 'gh auth login'."
                )
                return 1

            # Extract the content for this version from the updated changelog
            if version_content := extract_version_content(version):
                update_github_release(
                    version, version_content, repo_url, dry_run=args.dry_run, open_url=args.open
                )

        return 0
    except Exception as e:
        logger.error("Failed to update changelog: %s", str(e))
        return 1


if __name__ == "__main__":
    main()
