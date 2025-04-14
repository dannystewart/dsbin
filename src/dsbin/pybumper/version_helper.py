from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dsbin.pybumper.bump_type import BumpType

if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path


@dataclass
class Version:
    """Represents a parsed version."""

    version_string: str
    major: int
    minor: int
    patch: int
    pre_type: BumpType | None
    pre_num: int | None

    def __str__(self) -> str:
        return self.version_string


@dataclass
class VersionHelper:
    """Helper class for version-related operations."""

    pyproject_path: Path
    logger: Logger

    def get_version(self) -> str:
        """Get current version from pyproject.toml."""
        content = self.pyproject_path.read_text()
        try:
            import tomllib

            data = tomllib.loads(content)
            if "project" in data and "version" in data["project"]:
                return data["project"]["version"]
            self.logger.error("Could not find version in pyproject.toml (project.version).")
            sys.exit(1)
        except tomllib.TOMLDecodeError:
            self.logger.error(
                "Invalid TOML format in pyproject.toml. Do you even know how to use a text editor?"
            )
            sys.exit(1)

    def get_version_object(self) -> Version:
        """Get current version from pyproject.toml as a Version object."""
        version_str = self.get_version()
        return self.parse_version(version_str)

    def parse_version(self, version_str: str) -> Version:
        """Parse version string into a Version object."""
        major, minor, patch, pre_type, pre_num = self._parse_version_components(version_str)
        return Version(version_str, major, minor, patch, pre_type, pre_num)

    def _parse_version_components(
        self, version: str
    ) -> tuple[int, int, int, BumpType | None, int | None]:
        """Parse version string into components.

        Args:
            version: The version string (e.g., '1.2.3', '1.2.3a1', '1.2.3.post1').

        Returns:
            A tuple of (major, minor, patch, pre-release type, pre-release number).
        """
        # Try each version format parser in sequence
        if ".post" in version:
            return self._parse_post_version(version)
        if ".dev" in version:
            return self._parse_dev_version(version)

        # Try pre-release suffixes (alpha, beta, rc)
        pre_release_result = self._try_parse_prerelease(version)
        if pre_release_result:
            return pre_release_result

        # Handle plain version (major.minor.patch)
        return self._parse_plain_version(version)

    def _parse_post_version(self, version: str) -> tuple[int, int, int, BumpType, int]:
        """Parse a post-release version string."""
        version_part, post_num = version.rsplit(".post", 1)
        try:
            pre_num = int(post_num)
        except ValueError:
            self.logger.error("Invalid post-release number: %s", post_num)
            sys.exit(1)

        major, minor, patch = self._parse_version_parts(version_part)
        return major, minor, patch, BumpType.POST, pre_num

    def _parse_dev_version(self, version: str) -> tuple[int, int, int, BumpType, int]:
        """Parse a development version string."""
        # Split on .dev to get the base version part and dev number
        parts = version.split(".dev")
        version_part = parts[0]

        # Handle .dev without a number (implicit 0)
        if len(parts) == 1 or not parts[1]:
            dev_num = 0
        else:
            try:
                dev_num = int(parts[1])
            except ValueError:
                self.logger.error("Invalid dev number: %s", parts[1])
                sys.exit(1)

        major, minor, patch = self._parse_version_parts(version_part)
        return major, minor, patch, BumpType.DEV, dev_num

    def _try_parse_prerelease(self, version: str) -> tuple[int, int, int, BumpType, int] | None:
        """Try to parse a pre-release version string (alpha, beta, rc).

        Returns:
            A tuple of version components if it's a pre-release, or None.
        """
        suffix_map = {"a": BumpType.ALPHA, "b": BumpType.BETA, "rc": BumpType.RC}

        for suffix, bump_type in suffix_map.items():
            if suffix in version:
                try:
                    version_part, pre_num_str = version.rsplit(suffix, 1)
                    pre_num = int(pre_num_str)
                    major, minor, patch = self._parse_version_parts(version_part)
                    return major, minor, patch, bump_type, pre_num
                except ValueError:
                    self.logger.error("Invalid pre-release number: %s", pre_num_str)
                    sys.exit(1)

        # Not a pre-release version
        return None

    def _parse_plain_version(self, version: str) -> tuple[int, int, int, None, None]:
        """Parse a plain version string without any suffixes."""
        try:
            major, minor, patch = self._parse_version_parts(version)
            return major, minor, patch, None, None
        except ValueError:
            self.logger.error(
                "Invalid version format: %s. Numbers go left to right, champ.", version
            )
            sys.exit(1)

    def _parse_version_parts(self, version_part: str) -> tuple[int, int, int]:
        """Parse major.minor.patch components from a version string."""
        components = version_part.split(".")
        if len(components) != 3:
            self.logger.error("Invalid version format: %s. Expected x.y.z format.", version_part)
            sys.exit(1)

        try:
            major, minor, patch = map(int, components)
            return major, minor, patch
        except ValueError:
            self.logger.error(
                "Invalid version numbers in: %s. Version components must be integers.", version_part
            )
            sys.exit(1)

    def bump_version(self, bump_type: BumpType | str, version: Version) -> Version | None:
        """Calculate new version based on bump type and current version.

        Args:
            bump_type: Version bump type (major/minor/patch/alpha/beta/rc) or specific version.
            version: Current version object.

        Returns:
            New version object.
        """
        # Handle explicit version numbers
        if bump_type.count(".") >= 2:
            self._handle_explicit_version(bump_type)
            new_version_str = bump_type
            return self.parse_version(new_version_str)

        # Convert to enum if it's a string
        bump_type_enum = BumpType(bump_type) if not isinstance(bump_type, BumpType) else bump_type

        # Handle different bump types
        if bump_type_enum == BumpType.MAJOR:
            # Major bump resets minor and patch to 0
            new_version_str = f"{version.major + 1}.0.0"
            return self.parse_version(new_version_str)

        if bump_type_enum == BumpType.MINOR:
            # Minor bump resets patch to 0
            new_version_str = f"{version.major}.{version.minor + 1}.0"
            return self.parse_version(new_version_str)

        if bump_type_enum == BumpType.PATCH:
            # For a patch bump, we need to check if we're finalizing a pre-release
            if version.pre_type and version.pre_type.is_prerelease:
                # Finalizing a pre-release - keep same version but drop pre-release suffix
                new_version_str = f"{version.major}.{version.minor}.{version.patch}"
            else:
                # Regular patch bump
                new_version_str = f"{version.major}.{version.minor}.{version.patch + 1}"
            return self.parse_version(new_version_str)

        # Handle pre-release and post-release bumps
        if bump_type_enum.is_prerelease or bump_type_enum == BumpType.POST:
            # For dev, alpha, beta, rc, post
            return self._handle_version_modifier(bump_type_enum, version)

        self.logger.error("Invalid bump type: %s", bump_type)
        sys.exit(1)

    def _handle_special_bump(self, bump_type: BumpType | str, version: Version) -> Version:
        """Handle special bump types like dev, alpha, beta, rc, post."""
        bump_type_enum = BumpType(bump_type) if not isinstance(bump_type, BumpType) else bump_type

        # Determine what the next version should be based on the bump type
        if bump_type_enum == BumpType.DEV:
            # For dev versions, we want to start with .dev0
            new_version_str = f"{version.major}.{version.minor}.{version.patch}.dev0"
        elif bump_type_enum.is_prerelease:
            # For other pre-releases, we increment to the next version
            new_version_str = (
                f"{version.major}.{version.minor}.{version.patch}{bump_type_enum.version_suffix}1"
            )
        elif bump_type_enum == BumpType.POST:
            # For post-releases, we add .post1
            new_version_str = f"{version.major}.{version.minor}.{version.patch}.post1"
        else:
            self.logger.error("Invalid bump type for post-release: %s", bump_type)
            sys.exit(1)

        return self.parse_version(new_version_str)

    def _get_base_version(self, bump_type: BumpType | str, version: Version) -> Version:
        """Calculate base version based on bump type."""
        if bump_type.count(".") >= 2:
            return self.parse_version(bump_type)

        # Now we know it's a BumpType
        bump_type_enum = BumpType(bump_type) if not isinstance(bump_type, BumpType) else bump_type

        # Handle pre-release bumping
        if bump_type_enum.is_prerelease or bump_type_enum == BumpType.POST:
            return self._handle_version_modifier(bump_type_enum, version)

        # When moving from pre-release to release
        if version.pre_type and bump_type_enum == BumpType.PATCH:
            new_version_str = f"{version.major}.{version.minor}.{version.patch}"
            return self.parse_version(new_version_str)

        # Handle regular version bumping
        match bump_type_enum:
            case BumpType.MAJOR:
                new_version_str = f"{version.major + 1}.0.0"
            case BumpType.MINOR:
                new_version_str = f"{version.major}.{version.minor + 1}.0"
            case BumpType.PATCH:
                new_version_str = f"{version.major}.{version.minor}.{version.patch + 1}"
            case _:
                self.logger.error("Invalid bump type: %s", bump_type)
                sys.exit(1)

        return self.parse_version(new_version_str)

    def _handle_explicit_version(self, version: str) -> None:
        """Validate explicit version number format."""
        # Parse version to extract the base part (major.minor.patch)
        major, minor, patch, _, _ = self._parse_version_components(version)

        # Validate the numbers
        if any(n < 0 for n in (major, minor, patch)):
            self.logger.error("Invalid version number: %s. Numbers cannot be negative.", version)
            sys.exit(1)

    def _handle_version_modifier(self, bump_type: BumpType, version: Version) -> Version:
        """Calculate pre-release version bump."""
        if bump_type == BumpType.POST:
            return self._handle_post_release(version)

        if bump_type == BumpType.DEV:
            return self._handle_dev_release(version)

        # Handle alpha, beta, rc
        return self._handle_prerelease(bump_type, version)

    def _handle_post_release(self, version: Version) -> Version:
        """Handle post-release version bump."""
        if version.pre_type == BumpType.POST and version.pre_num:
            # Increment existing post-release
            new_version_str = (
                f"{version.major}.{version.minor}.{version.patch}.post{version.pre_num + 1}"
            )
        elif version.pre_type and version.pre_type.is_prerelease:
            # Can't add post-release to pre-release
            self.logger.error(
                "Can't add post-release to %s%s, genius. "
                "How can you post-release something that isn't released? "
                "Finalize the version first.",
                version.pre_type,
                version.pre_num,
            )
            sys.exit(1)
        else:
            # Add post-release to regular version
            new_version_str = f"{version.major}.{version.minor}.{version.patch}.post0"

        return self.parse_version(new_version_str)

    def _handle_dev_release(self, version: Version) -> Version:
        """Handle dev version bump."""
        if version.pre_type == BumpType.DEV and version.pre_num is not None:
            # Increment existing dev version
            new_version_str = (
                f"{version.major}.{version.minor}.{version.patch}.dev{version.pre_num + 1}"
            )
        else:
            # Start new dev series
            new_version_str = f"{version.major}.{version.minor}.{version.patch}.dev"

        return self.parse_version(new_version_str)

    def _handle_prerelease(self, bump_type: BumpType, version: Version) -> Version:
        """Handle alpha, beta, rc version bumps."""
        new_suffix = bump_type.version_suffix

        # Check for invalid progression
        if version.pre_type and version.pre_type.sort_value() > bump_type.sort_value():
            self.logger.error(
                "Can't go backwards from %s to %s, idiot. Version progression is: dev -> alpha -> beta -> rc",
                version.pre_type.version_suffix,
                new_suffix,
            )
            sys.exit(1)

        # Determine the new version string
        if version.pre_type == bump_type and version.pre_num is not None:
            # Increment same pre-release type (e.g., beta1 -> beta2)
            new_version_str = (
                f"{version.major}.{version.minor}.{version.patch}{new_suffix}{version.pre_num + 1}"
            )
        elif version.pre_type and version.pre_type.is_prerelease and version.pre_type != bump_type:
            # Progress to next pre-release stage (e.g., alpha1 -> beta1)
            new_version_str = f"{version.major}.{version.minor}.{version.patch}{new_suffix}1"
        else:
            # Start new pre-release series
            if not version.pre_type and version.patch != 0:
                patch = version.patch + 1
            else:
                patch = version.patch
            new_version_str = f"{version.major}.{version.minor}.{patch}{new_suffix}1"

        return self.parse_version(new_version_str)

    def parse_bump_types(self, type_args: list[str]) -> BumpType | list[BumpType] | str:
        """Parse bump type arguments into appropriate format."""
        # Handle explicit version case
        if len(type_args) == 1 and type_args[0].count(".") >= 2:
            return type_args[0]

        # Handle multiple bump types
        bump_types = []
        for t in type_args:
            if hasattr(BumpType, t.upper()):
                bump_types.append(BumpType(t))
            else:
                self.logger.error(
                    "Invalid argument: %s. Must be a bump type (%s) or version number (x.y.z)",
                    t,
                    ", ".join(item.value for item in BumpType),
                )
                sys.exit(1)

        return bump_types if len(bump_types) > 1 else bump_types[0]

    @staticmethod
    def detect_version_prefix() -> str:
        """Detect whether versions are tagged with 'v' prefix based on existing tags."""
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

            # If no matching tags found, default to 'v' prefix
            return "v"

        except subprocess.CalledProcessError:
            # If git commands fail, default to 'v' prefix
            return "v"
