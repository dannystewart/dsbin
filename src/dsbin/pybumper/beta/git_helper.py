from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import confirm_action
from polykit.shell import handle_interrupt

from dsbin.pybumper.beta.monorepo_helper import MonorepoHelperBeta

if TYPE_CHECKING:
    from logging import Logger

    from dsbin.pybumper.bump_type import BumpType
    from dsbin.pybumper.version_helper import VersionHelper


@dataclass
class GitHelperBeta:
    """Helper class for git operations."""

    version_helper: VersionHelper
    logger: Logger
    commit_message: str | None = None
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
    def tag_current_version(self, package_name: str) -> None:
        """Tag and push the current version without incrementing.

        Creates a new commit with the current version number, then tags and pushes it.

        Raises:
            CalledProcessError: If any of the git commands fail.
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

        # Create a new commit with the current version number if there are changes
        try:
            has_other_changes = self.commit_version_change(current_version, package_name)
            if has_other_changes:
                self.logger.warning(
                    "Committed pyproject.toml without version change. "
                    "Other changes in the working directory will be preserved."
                )
                if not confirm_action("Commit and push anyway?", prompt_color="yellow"):
                    self.logger.warning("Bump aborted.")
                    sys.exit(1)
        except subprocess.CalledProcessError as e:
            # If there are no changes to commit, just proceed with tagging
            if "nothing to commit" in str(e):
                self.logger.info("No changes to commit, proceeding with tagging.")
            else:
                raise

        # Create tag
        subprocess.run(["git", "tag", tag_name], check=True)

        if self.push_to_remote:  # Push changes and tags
            subprocess.run(["git", "push"], check=True)
            subprocess.run(["git", "push", "--tags"], check=True)
            self.logger.info("Successfully tagged and pushed version %s!", current_version)
        else:
            self.logger.info(
                "Successfully tagged version %s! Use 'git push && git push --tags' to push to remote.",
                current_version,
            )

    def commit_version_change(self, new_version: str, package_name: str) -> bool:
        """Commit version change to git.

        Args:
            new_version: The new version string.
            package_name: The name of the package being versioned.

        Returns:
            True if there were other uncommitted changes, False otherwise.
        """
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )

        # Check if pyproject.toml has changes
        pyproject_changed = any(
            line.endswith("pyproject.toml") for line in result.stdout.splitlines()
        )

        if not pyproject_changed:
            self.logger.info("No changes to pyproject.toml detected.")
            return False

        has_other_changes = any(
            not line.endswith("pyproject.toml") for line in result.stdout.splitlines()
        )

        # Stage only pyproject.toml
        subprocess.run(["git", "add", "pyproject.toml"], check=True)

        # Determine if we're in a monorepo
        current_dir = Path.cwd()
        monorepo_root = MonorepoHelperBeta.find_monorepo_root(current_dir)

        # Use custom message if provided, otherwise use default
        if self.commit_message:
            message = self.commit_message
        elif monorepo_root:
            message = f"Bump {package_name} to {new_version}"
        else:
            message = f"Bump version to {new_version}"

        subprocess.run(["git", "commit", "-m", message], check=True)

        return has_other_changes

    def generate_tag_name(self, version: str, package_name: str) -> str:
        """Generate tag name for the given version and package.

        Args:
            version: The version string.
            package_name: The package name.

        Returns:
            The tag name in format 'package_name-vX.Y.Z' for monorepo or 'vX.Y.Z' for standard repo.
        """
        version_prefix = self.detect_version_prefix()

        # Determine if we're in a monorepo
        current_dir = Path.cwd()
        monorepo_root = MonorepoHelperBeta.find_monorepo_root(current_dir)

        if monorepo_root:
            # We're in a monorepo, use package-specific tag
            return f"{package_name}-{version_prefix}{version}"
        # Standard repository, use simple version tag
        return f"{version_prefix}{version}"

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
        package_name: str,
    ) -> None:
        """Handle git commit, tag, and push operations.

        Args:
            new_version: The version string to tag with.
            bump_type: The type of version bump performed.
            package_name: The name of the package being versioned.
        """
        version_prefix = self.detect_version_prefix()
        tag_name = f"{version_prefix}{new_version}"

        # Handle version bump commit if needed
        if bump_type is not None:
            # Check for uncommitted changes BEFORE making any commits
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
            )
            has_other_changes = any(
                not line.endswith("pyproject.toml") for line in result.stdout.splitlines()
            )

            if has_other_changes:
                self.logger.warning(
                    "There are uncommitted changes in the working directory besides pyproject.toml."
                )
                if not confirm_action("Continue with version bump anyway?", prompt_color="yellow"):
                    self.logger.warning("Version bump aborted.")
                    sys.exit(1)

            # Now proceed with the commit
            has_other_changes = self.commit_version_change(new_version, package_name)
            if has_other_changes:
                self.logger.info(
                    "Committed pyproject.toml with the version bump. "
                    "Other changes in the working directory were skipped and preserved."
                )

        # Check if tag already exists
        if (
            subprocess.run(
                ["git", "rev-parse", tag_name], capture_output=True, check=False
            ).returncode
            == 0
        ):
            self.logger.error("Tag %s already exists.", tag_name)
            sys.exit(1)

        # Create tag
        subprocess.run(["git", "tag", tag_name], check=True)

        if self.push_to_remote:  # Push changes and tags
            subprocess.run(["git", "push"], check=True)
            subprocess.run(["git", "push", "--tags"], check=True)
        else:
            self.logger.info(
                "Changes committed and tagged locally. Use 'git push && git push --tags' to push to remote."
            )
