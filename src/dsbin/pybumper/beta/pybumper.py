"""Version management tool for Python projects."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from dsbase import EnvManager, LocalLogger, Text
from dsbase.shell import confirm_action
from dsbase.util import dsbase_setup, handle_interrupt

from dsbin.pybumper.beta.git_helper import GitHelper
from dsbin.pybumper.bump_type import BumpType
from dsbin.pybumper.version_helper import VersionHelper

if TYPE_CHECKING:
    import argparse

dsbase_setup()


class PyBumper:
    """Version management tool for Python projects."""

    def __init__(self, args: argparse.Namespace, package_name: str) -> None:
        # Use EnvManager for debug flag
        env = EnvManager()
        env.add_debug_var()

        # Create logger with debug flag; use simple logger if debug is off
        self.logger = LocalLogger().get_logger(env.log_level, simple=not env.debug)

        # Parse command-line arguments into instance variables
        self.no_increment = args.no_increment
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

        # Store package name
        self.package_name = package_name

        # Get current version as a Version object
        self.current_version = self.version_helper.get_version_object()
        self.current_ver_str = str(self.current_version)

    def perform_bump(self) -> None:
        """Perform version bump."""
        try:
            # Handle --no-increment flag (tag current version without incrementing)
            if self.no_increment:
                if self.type and self.type != [BumpType.PATCH.value]:
                    self.logger.error("--no-increment cannot be used with version bump arguments")
                    sys.exit(1)
                self.git.tag_current_version(self.package_name)
                return

            # Default to patch if no types specified
            type_args = self.type or [BumpType.PATCH.value]
            bump_type = self.version_helper.parse_bump_types(type_args)

            # Calculate new version
            new_version_obj = self.current_version

            # If we have multiple bump types, sort them in a consistent order
            if isinstance(bump_type, list):
                # Sort and apply bumps in logical order
                sorted_bumps = self._sort_bump_types(bump_type)
                for bt in sorted_bumps:
                    new_version_obj = self.version_helper.bump_version(bt, new_version_obj)
            else:
                new_version_obj = self.version_helper.bump_version(bump_type, self.current_version)

            new_version_str = str(new_version_obj)
            tag_name = self.git.generate_tag_name(new_version_str, self.package_name)

            # Show version info
            self.logger.info("Package:         %s", Text.color(self.package_name, "yellow"))
            self.logger.info("Current version: %s", Text.color(self.current_ver_str, "cyan"))
            self.logger.info("Will bump to:    %s", Text.color(new_version_str, "blue"))
            self.logger.info("Tag name:        %s", Text.color(tag_name, "green"))

            # Prompt for confirmation unless --force is used
            if not self.force:
                if not confirm_action(f"Proceed with version bump for {self.package_name}?"):
                    self.logger.info("Version bump canceled.")
                    return

            self.update_version(bump_type, new_version_str)
        except Exception as e:
            self.logger.error(str(e))
            sys.exit(1)

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
    def update_version(self, bump_type: BumpType | str | list[BumpType], new_version: str) -> None:
        """Update version, create git tag, and push changes."""
        try:
            self.git.check_git_state()

            # Update version in pyproject.toml
            if bump_type is not None:
                self._update_version_in_pyproject(self.pyproject_path, new_version)

            # Handle git operations with package name
            self.git.handle_git_operations(new_version, bump_type, self.package_name)

            # Log success
            action = "tagged" if bump_type is None else "updated to"
            push_status = "" if self.push_to_remote else " (not pushed)"
            self.logger.info("Successfully %s v%s%s!", action, new_version, push_status)

        except Exception as e:
            self.logger.error("Version update failed: %s", str(e))
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
