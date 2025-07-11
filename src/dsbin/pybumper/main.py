"""Version management tool for Python projects.

Handles version bumping, pre-releases, development versions, and git operations following PEP 440.
Supports major.minor.patch versioning with dev/alpha/beta/rc prerelease (and post-release) versions.

Usage:
    # Regular version bumping
    pybumper                # 1.2.3    -> 1.2.4
    pybumper minor          # 1.2.3    -> 1.3.0
    pybumper major          # 1.2.3    -> 2.0.0

    # Pre-release versions
    pybumper dev            # 1.2.3    -> 1.2.4.dev0
    pybumper alpha          # 1.2.3    -> 1.2.4a1
    pybumper beta           # 1.2.4a1  -> 1.2.4b1
    pybumper rc             # 1.2.4b1  -> 1.2.4rc1
    pybumper patch          # 1.2.4rc1 -> 1.2.4

    # Post-release version
    pybumper post           # 1.2.4    -> 1.2.4.post1

    # File-only operations
    pybumper -i             # 1.2.3    -> 1.2.4 (pyproject.toml only)
    pybumper -i minor       # 1.2.3    -> 1.3.0 (pyproject.toml only)

All operations include git tagging and pushing changes to remote repository, except when using
--increment-only which only updates pyproject.toml.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from polykit import PolyArgs, PolyLog
from polykit.cli import confirm_action, handle_interrupt
from polykit.core import polykit_setup
from polykit.env import PolyEnv

from dsbin.pybumper.bump_type import BumpType
from dsbin.pybumper.git_helper import GitHelper
from dsbin.pybumper.version_helper import Version, VersionHelper

if TYPE_CHECKING:
    import argparse

polykit_setup()


class PyBumper:
    """Version management tool for Python projects."""

    def __init__(self, args: argparse.Namespace) -> None:
        # Create PolyEnv to manage debug flag
        env = PolyEnv()
        env.add_debug_var()

        # Create logger with debug flag; use simple logger if debug is off
        self.logger = PolyLog.get_logger(
            level="debug" if env.debug else "info", simple=not env.debug
        )

        # Parse command-line arguments into instance variables
        self.no_increment = args.no_increment
        self.increment_only = args.increment_only
        self.force = args.force
        self.type = args.type

        # Whether to push changes to remote (default is True unless --no-push is specified)
        self.push_to_remote = not args.no_push

        # Verify and load pyproject.toml
        self.pyproject_path = Path("pyproject.toml")
        if not self.pyproject_path.exists():
            self.logger.error("No pyproject.toml found in current directory.")
            sys.exit(1)

        # Initialize helpers
        self.version_helper = VersionHelper(self.pyproject_path, self.logger)
        self.git = GitHelper(self.version_helper, self.logger, args.message, self.push_to_remote)

        # Get current version as a Version object
        self.current_version = self.version_helper.get_version_object()
        self.current_ver_str = str(self.current_version)

    def perform_bump(self) -> None:
        """Perform version bump."""
        try:
            # Handle --increment-only flag (increment version in pyproject.toml only)
            if self.increment_only:
                if self.no_increment:
                    self.logger.error("--increment-only cannot be used with --no-increment")
                    sys.exit(1)
                self.perform_increment_only()
                return

            # Handle --no-increment flag (tag current version without incrementing)
            if self.no_increment:
                if self.type and self.type != [BumpType.PATCH.value]:
                    self.logger.error("--no-increment cannot be used with version bump arguments")
                    sys.exit(1)
                self.git.tag_current_version()
                return

            # Calculate new version
            new_version_obj = self._calculate_new_version()
            if new_version_obj is None:
                return

            new_version_str = str(new_version_obj)

            # Show version info and get confirmation
            if not self._confirm_version_bump(new_version_str):
                return

            # Calculate next dev version if needed
            next_dev_version = self._calculate_next_dev_version(new_version_obj)

            # Default to patch if no types specified
            type_args = self.type or [BumpType.PATCH.value]
            bump_type = self.version_helper.parse_bump_types(type_args)

            self.update_version(bump_type, new_version_str, next_dev_version)
        except Exception as e:
            self.logger.error(str(e))
            sys.exit(1)

    def perform_increment_only(self) -> None:
        """Increment version in pyproject.toml only, no git operations."""
        # Calculate new version
        new_version_obj = self._calculate_new_version()
        if new_version_obj is None:
            return

        new_version_str = str(new_version_obj)

        # Show version info and get confirmation
        self.logger.info("Current version: %s", self.current_ver_str)
        self.logger.info("Will bump to:    %s", new_version_str)

        # Prompt for confirmation unless --force is used
        if not self.force and not confirm_action("Proceed with version increment?"):
            self.logger.info("Version increment canceled.")
            return

        # Update version in pyproject.toml only
        self._update_version_in_pyproject(self.pyproject_path, new_version_str)

        # Log success
        self.logger.info("\nSuccessfully incremented version to %s!", new_version_str)

    def _calculate_new_version(self) -> Version | None:
        """Calculate the new version based on bump types."""
        # Default to patch if no types specified
        type_args = self.type or [BumpType.PATCH.value]
        bump_type = self.version_helper.parse_bump_types(type_args)

        new_version_obj = self.current_version

        # If we have multiple bump types, sort them in a consistent order
        if isinstance(bump_type, list):
            # Sort and apply bumps in logical order
            sorted_bumps = self._sort_bump_types(bump_type)
            for bt in sorted_bumps:
                bumped_version = self.version_helper.bump_version(bt, new_version_obj)
                if bumped_version is None:
                    self.logger.error("Failed to bump version with type %s", bt)
                    return None
                new_version_obj = bumped_version
        else:
            new_version_obj = self.version_helper.bump_version(bump_type, self.current_version)

        return new_version_obj

    def _confirm_version_bump(self, new_version_str: str) -> bool:
        """Show version info and get user confirmation."""
        self.logger.info("Current version: %s", self.current_ver_str)
        self.logger.info("Will bump to:    %s", new_version_str)

        # Prompt for confirmation unless --force is used
        if not self.force and not confirm_action("Proceed with version bump?"):
            self.logger.info("Version bump canceled.")
            return False
        return True

    def _calculate_next_dev_version(self, new_version_obj: Version) -> str | None:
        """Calculate the next dev version for local use after release.

        Returns:
            str: The next dev version string if needed and successful.
            None: No dev version is needed, or an error occurred.
        """
        if not self.push_to_remote or new_version_obj.pre_type:
            return None

        # Only for final releases that are being pushed
        next_dev_version_obj = self.version_helper.bump_version(BumpType.PATCH, new_version_obj)
        if next_dev_version_obj is None:
            self.logger.error("Failed to bump version for next dev version")
            return None

        next_dev_version_obj = self.version_helper.bump_version(BumpType.DEV, next_dev_version_obj)
        if next_dev_version_obj is None:
            self.logger.error("Failed to bump dev version")
            return None

        return str(next_dev_version_obj)

    def _sort_bump_types(self, bump_types: list[BumpType]) -> list[BumpType]:
        """Sort bump types in logical order: major/minor/patch, then pre-release, then post."""
        # First apply all regular version bumps (major, minor, patch) in that order
        regular_bumps = [bt for bt in bump_types if bt.is_release]
        # Sort by priority (major > minor > patch)
        regular_bumps.sort(reverse=True)

        # Then apply all pre-release bumps in order (dev, alpha, beta, rc)
        prerelease_bumps = [bt for bt in bump_types if bt.is_prerelease]
        prerelease_bumps.sort()

        # Finally apply post if present
        post_bumps = [bt for bt in bump_types if bt == BumpType.POST]

        # Combine in the right order
        return regular_bumps + prerelease_bumps + post_bumps

    @handle_interrupt()
    def update_version(
        self,
        bump_type: BumpType | str | list[BumpType] | None,
        new_version: str,
        next_dev_version: str | None = None,
    ) -> None:
        """Update version, create git tag, and push changes.

        Args:
            bump_type: The version's BumpType or list of BumpTypes, or a specific version string.
            new_version: The calculated new version string.
            next_dev_version: Optional next development version to set locally after pushing.
        """
        try:
            self.git.check_git_state()

            # Update version in pyproject.toml
            if bump_type is not None:
                self._update_version_in_pyproject(self.pyproject_path, new_version)

            # Handle git operations
            self.git.handle_git_operations(new_version, bump_type)

            # After successful push, update local version to next dev version
            if next_dev_version is not None:
                self.logger.debug("Setting local version to dev version %s.", next_dev_version)
                self._update_version_in_pyproject(self.pyproject_path, next_dev_version)

                # Add a second commit for the dev version
                self.git.commit_dev_version(next_dev_version)

            # Push all commits and tags once at the end if enabled
            if self.push_to_remote:
                self.git.push_all()
            else:
                self.logger.debug("Version changes committed and tagged.")

            # Log success
            action = "tagged" if bump_type is None else "updated to"
            push_status = "" if self.push_to_remote else " (not pushed)"
            release_msg = f"v{new_version}"
            dev_msg = f"\nNext version: {next_dev_version}" if next_dev_version is not None else ""
            self.logger.info("\nSuccessfully %s %s!%s", action, release_msg, push_status + dev_msg)

        except Exception as e:
            self.logger.error("\nVersion update failed: %s", str(e))
            raise

    def _update_version_in_pyproject(self, pyproject: Path, new_version: str) -> None:
        """Update version in pyproject.toml while preserving formatting."""
        content = pyproject.read_text()
        lines = content.splitlines()

        # Find the version line
        version_line_idx = None
        in_project = False

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("[project]"):
                in_project = True
            elif stripped.startswith("["):  # Any other section
                in_project = False

            if in_project and stripped.startswith("version"):
                version_line_idx = i
                break

        if version_line_idx is None:
            self.logger.error("Could not find version field in project section.")
            sys.exit(1)

        # Update the version line while preserving indentation
        current_line = lines[version_line_idx]
        if "=" in current_line:
            before_version = current_line.split("=")[0]
            quote_char = '"' if '"' in current_line else "'"
            lines[version_line_idx] = f"{before_version}= {quote_char}{new_version}{quote_char}"

        # Verify the new content is valid TOML before writing
        new_content = "\n".join(lines) + "\n"
        try:
            import tomllib

            tomllib.loads(new_content)
        except tomllib.TOMLDecodeError:
            self.logger.error("Version update would create invalid TOML. Aborting.")
            sys.exit(1)

        # Write back the file
        pyproject.write_text(new_content)

        # Verify the changes
        if self.version_helper.get_version() != new_version:
            self.logger.error("Version update failed verification.")
            sys.exit(1)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description=__doc__, lines=1, arg_width=34)
    parser.add_argument(
        "type",
        nargs="*",
        default=[BumpType.PATCH],
        help="major, minor, patch, dev, alpha, beta, rc, post; or x.y.z",
    )
    parser.add_argument("-f", "--force", action="store_true", help="skip confirmation prompt")
    parser.add_argument(
        "-m", "--message", help="custom commit message (default: 'chore(version): bump to x.y.z')"
    )

    # Mutually exclusive group for push options
    push_group = parser.add_mutually_exclusive_group()
    push_group.add_argument(
        "--no-increment",
        action="store_true",
        help="do not increment version; just commit, tag, and push",
    )
    push_group.add_argument(
        "--no-push",
        action="store_true",
        help="increment version, commit, and tag; do not push",
    )
    push_group.add_argument(
        "-i",
        "--increment-only",
        action="store_true",
        help="increment version in pyproject.toml only; no git operations",
    )

    return parser.parse_args()


def main() -> None:
    """Perform version bump."""
    args = parse_args()
    PyBumper(args).perform_bump()


if __name__ == "__main__":
    main()
