from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from dsbase.util import handle_interrupt

from dsbin.dsbump.bump_type import BumpType

if TYPE_CHECKING:
    from logging import Logger

    from dsbin.dsbump.version_helper import VersionHelper


@dataclass
class GitHelper:
    """Helper class for git operations."""

    version_helper: VersionHelper
    logger: Logger
    commit_message: str | None = None
    cleanup: bool = False
    push_to_remote: bool = True

    @handle_interrupt()
    def check_git_state(self) -> None:
        """Check if we're in a git repository and on a valid branch."""
        try:  # Check if we're in a git repo
            subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.logger.error("Not a git repository.")
            sys.exit(1)

        # Check if we're on a branch (not in detached HEAD state)
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            self.logger.error("Not on a git branch (detached HEAD state).")
            sys.exit(1)

    @handle_interrupt()
    def detect_version_prefix(self) -> str:
        """Detect whether versions are tagged with 'v' prefix based on existing tags.

        Returns:
            "v" if versions use v-prefix, "" if they use bare numbers
        """
        try:
            # Get all tags sorted by version
            result = subprocess.run(
                ["git", "tag", "--sort=v:refname"], capture_output=True, text=True, check=True
            )
            tags = result.stdout.strip().split("\n")

            # Filter out empty results
            tags = [tag for tag in tags if tag]
            if not tags:
                # Default to "v" prefix for new projects
                return "v"

            # Look at the most recent tag that starts with either v or a number
            for tag in reversed(tags):
                if tag.startswith("v") or tag[0].isdigit():
                    return "v" if tag.startswith("v") else ""

            # If no matching tags found, default to "v" prefix
            return "v"

        except subprocess.CalledProcessError:
            # If git commands fail, default to "v" prefix
            return "v"

    @handle_interrupt()
    def tag_current_version(self) -> None:
        """Tag and push the current version without incrementing.

        Creates a new commit with the current version number, then tags and pushes it.

        Args:
            commit_message: Custom commit message (if None, default is used).
        """
        pyproject = Path("pyproject.toml")
        if not pyproject.exists():
            self.logger.error("No pyproject.toml found in current directory.")
            sys.exit(1)

        self.check_git_state()
        current_version = self.version_helper.get_version()
        version_prefix = self.detect_version_prefix()
        tag_name = f"{version_prefix}{current_version}"

        # Check if tag already exists
        if (
            subprocess.run(
                ["git", "rev-parse", tag_name], capture_output=True, check=False
            ).returncode
            == 0
        ):
            self.logger.error("Tag %s already exists.", tag_name)
            sys.exit(1)

        # Create a new commit with the current version number
        has_other_changes = self.commit_version_change(current_version)
        if has_other_changes:
            self.logger.info(
                "Committed pyproject.toml without version change. "
                "Other changes in the working directory were skipped and preserved."
            )

        # Create tag
        subprocess.run(["git", "tag", tag_name], check=True)

        # Push changes and tags
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)

        self.logger.info("Successfully tagged and pushed version %s!", current_version)

    @handle_interrupt()
    def cleanup_tags(self, old_ver: str, new_ver: str) -> None:
        """Remove all pre-release tags for relevant versions.

        Removes tags based on version bump type:
        - Major bump (1.x -> 2.x): Removes all 1.x pre-release tags
        - Minor bump (1.1 -> 1.2): Removes all 1.1.x pre-release tags
        - Patch bump (1.1.1 -> 1.1.2): Removes only 1.1.2 pre-release tags
        """
        self.logger.debug(
            "Checking for pre-release tags to clean up when moving from %s to %s.",
            old_ver,
            new_ver,
        )

        patterns = self._identify_tag_patterns(old_ver, new_ver)

        all_tags = set()
        for pattern in patterns:
            result = subprocess.run(
                ["git", "tag", "-l", pattern], capture_output=True, text=True, check=True
            )
            tags = result.stdout.strip().split("\n")
            if tags and tags[0]:  # Check if we actually found any tags
                all_tags.update(tags)

        if all_tags:
            self.logger.info("Cleaning up %d pre-release tags.", len(all_tags))
            self._remove_found_tags(all_tags)

    def _identify_tag_patterns(self, old_ver: str, new_ver: str) -> list[str]:
        """Find tag patterns to clean up based on version bump.

        Determines which pre-release tags should be cleaned up based on the type of version bump
        (major/minor/patch).

        Returns:
            List of glob patterns matching tags to be removed.
        """
        old = self.version_helper.parse_version(old_ver)
        new = self.version_helper.parse_version(new_ver)

        version_prefix = self.detect_version_prefix()

        prerelease_patterns = [
            t.version_suffix + "*"
            for t in [BumpType.DEV, BumpType.ALPHA, BumpType.BETA, BumpType.RC]
        ]

        patterns = []
        if new.major > old.major:
            patterns.extend(
                f"{version_prefix}{old.major}.*{pattern}" for pattern in prerelease_patterns
            )
        elif new.minor > old.minor:
            patterns.extend(
                f"{version_prefix}{old.major}.{old.minor}.*{pattern}"
                for pattern in prerelease_patterns
            )
        else:
            patterns.extend(
                f"{version_prefix}{new.major}.{new.minor}.{new.patch}{pattern}"
                for pattern in prerelease_patterns
            )

        return patterns

    @handle_interrupt()
    def _remove_found_tags(self, found_tags: set[str]) -> None:
        """Remove identified pre-release tags.

        Removes tags both locally and from remote if it exists. Remote tag deletion failures are
        ignored as tags might not exist remotely.

        Args:
            found_tags: Set of tag names to remove.
        """
        # Remove local tags
        for tag in found_tags:
            self.logger.info("Removing tag: %s", tag)
            subprocess.run(["git", "tag", "-d", tag], check=True)

        # Remove remote tags if remote exists
        remote_check = subprocess.run(
            ["git", "remote"], capture_output=True, text=True, check=False
        )
        if remote_check.stdout.strip():
            self.logger.debug("Removing remote tags...")
            subprocess.run(
                ["git", "push", "--delete", "origin", *list(found_tags)],
                capture_output=True,
                check=False,
            )

    def commit_version_change(self, new_version: str) -> bool:
        """Commit version change to git.

        Args:
            new_version: The new version string.
            commit_message: Optional custom commit message.

        Returns:
            True if there were other uncommitted changes, False otherwise.
        """
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        has_other_changes = any(
            not line.endswith("pyproject.toml") for line in result.stdout.splitlines()
        )

        # Stage only pyproject.toml
        subprocess.run(["git", "add", "pyproject.toml"], check=True)

        # Use custom message if provided, otherwise use default
        message = self.commit_message or f"Bump version to {new_version}"
        subprocess.run(["git", "commit", "-m", message], check=True)

        return has_other_changes

    def should_perform_cleanup(
        self, bump_type: BumpType | str | list[BumpType] | None, new_ver: str
    ) -> bool:
        """Determine if tag cleanup should be performed.

        Args:
            bump_type: The type of version bump performed.
            new_ver: The new version string.
        """
        if isinstance(bump_type, list):
            # If the last bump type in the list isn't a pre-release, clean up tags
            if not bump_type:
                return False
            return not bump_type[-1].is_prerelease

        if isinstance(bump_type, BumpType):
            version = self.version_helper.parse_version(new_ver)
            # If new version is a release version
            return version.pre_type is None

        if isinstance(bump_type, str) and bump_type.count(".") >= 2:  # Explicit version
            return not any(
                t.version_suffix in bump_type
                for t in [BumpType.DEV, BumpType.ALPHA, BumpType.BETA, BumpType.RC]
            )

        return False

    def create_and_push_tag(self, tag_name: str) -> None:
        """Create and push a git tag."""
        if (  # Check if tag already exists
            subprocess.run(
                ["git", "rev-parse", tag_name], capture_output=True, check=False
            ).returncode
            == 0
        ):
            self.logger.error("Tag %s already exists.", tag_name)
            sys.exit(1)

        # Create tag and push
        subprocess.run(["git", "tag", tag_name], check=True)
        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)

    @handle_interrupt()
    def handle_git_operations(
        self,
        new_version: str,
        bump_type: BumpType | str | list[BumpType] | None,
        current_version: str,
    ) -> None:
        """Handle git commit, tag, and push operations.

        Args:
            new_version: The version string to tag with.
            bump_type: The type of version bump performed.
            current_version: The previous version string.
        """
        version_prefix = self.detect_version_prefix()
        tag_name = f"{version_prefix}{new_version}"

        # Handle version bump commit if needed
        if bump_type is not None:
            has_other_changes = self.commit_version_change(new_version)
            if has_other_changes:
                self.logger.info(
                    "Committed pyproject.toml with the version bump. "
                    "Other changes in the working directory were skipped and preserved."
                )

        # Clean up pre-release tags when moving to a release version (if cleanup=True)
        if self.cleanup and self.should_perform_cleanup(bump_type, new_version):
            self.cleanup_tags(current_version, new_version)

        # Create tag
        if (  # Check if tag already exists
            subprocess.run(
                ["git", "rev-parse", tag_name], capture_output=True, check=False
            ).returncode
            == 0
        ):
            self.logger.error("Tag %s already exists.", tag_name)
            sys.exit(1)

        subprocess.run(["git", "tag", tag_name], check=True)

        if self.push_to_remote:  # Push changes and tags
            subprocess.run(["git", "push"], check=True)
            subprocess.run(["git", "push", "--tags"], check=True)
        else:
            self.logger.info(
                "Changes committed and tagged locally. Use 'git push && git push --tags' to push to remote."
            )
