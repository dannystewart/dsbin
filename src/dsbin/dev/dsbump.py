"""Version management tool for Python projects.

Handles version bumping, pre-releases, development versions, and git operations following PEP 440.
Supports major.minor.patch versioning with dev/alpha/beta/rc prerelease (and post-release) versions.

Usage:
    # Regular version bumping
    dsbump                # 1.2.3 -> 1.2.4
    dsbump minor          # 1.2.3 -> 1.3.0
    dsbump major          # 1.2.3 -> 2.0.0

    # Pre-release versions
    dsbump dev            # 1.2.3 -> 1.2.4.dev1
    dsbump alpha          # 1.2.3 -> 1.2.4a1
    dsbump beta           # 1.2.4a1 -> 1.2.4b1
    dsbump rc             # 1.2.4b1 -> 1.2.4rc1
    dsbump patch          # 1.2.4rc1 -> 1.2.4

    # Post-release version
    dsbump post           # 1.2.4 -> 1.2.4.post1

    # Custom messages
    dsbump -m "New feature"
    dsbump -t "Release notes: Fixed critical issues"

All operations include git tagging and pushing changes to remote repository.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from enum import StrEnum
from functools import total_ordering
from pathlib import Path

from dsutil import configure_traceback
from dsutil.env import DSEnv
from dsutil.log import LocalLogger
from dsutil.shell import handle_keyboard_interrupt

configure_traceback()

env = DSEnv()
env.add_debug_var()

log_level = "debug" if env.debug else "info"
logger = LocalLogger().get_logger(level=log_level, simple=not env.debug)


@total_ordering
class BumpType(StrEnum):
    """Version bump types following PEP 440.

    Progression:
    - Pre-release: dev -> alpha -> beta -> rc
    - Release: patch -> minor -> major
    - Post-release: post (only after final release)
    """

    DEV = "dev"
    ALPHA = "alpha"
    BETA = "beta"
    RC = "rc"
    POST = "post"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"

    @property
    def is_prerelease(self) -> bool:
        """Whether this is a pre-release version type."""
        return self in {self.DEV, self.ALPHA, self.BETA, self.RC}

    @property
    def is_release(self) -> bool:
        """Whether this is a regular release version type."""
        return self in {self.PATCH, self.MINOR, self.MAJOR}

    @property
    def version_suffix(self) -> str:
        """Get the suffix used in version strings."""
        match self:
            case self.DEV:
                return ".dev"
            case self.ALPHA:
                return "a"
            case self.BETA:
                return "b"
            case self.RC:
                return "rc"
            case self.POST:
                return ".post"
            case _:
                return ""

    def sort_value(self) -> int:
        """Get numeric sort value for comparison."""
        order = {
            self.DEV: -1,
            self.ALPHA: 0,
            self.BETA: 1,
            self.RC: 2,
            self.POST: 10,
            self.PATCH: 3,
            self.MINOR: 4,
            self.MAJOR: 5,
        }
        return order[self]

    def __lt__(self, other: BumpType | str) -> bool:
        """Compare bump types for ordering."""
        try:
            other = BumpType(other)
        except ValueError:
            return NotImplemented
        return self.sort_value() < other.sort_value()

    def can_progress_to(self, other: BumpType) -> bool:
        """Check if this version type can progress to another."""
        # Can't go backwards in pre-release chain
        if self.is_prerelease and other.is_prerelease:
            return self.sort_value() < other.sort_value()

        # Can't add post-release to pre-release
        if self.is_prerelease and other == self.POST:
            return False

        # Can always go to a release version
        if other.is_release:
            return True

        # Can add post-release to release versions
        return bool(self.is_release and other == self.POST)


@handle_keyboard_interrupt()
def check_git_state() -> None:
    """Check if we're in a git repository and on a valid branch."""
    try:  # Check if we're in a git repo
        subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        logger.error("Not a git repository.")
        sys.exit(1)

    # Check if we're on a branch (not in detached HEAD state)
    result = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        logger.error("Not on a git branch (detached HEAD state).")
        sys.exit(1)


@handle_keyboard_interrupt()
def detect_version_prefix() -> str:
    """Detect whether versions are tagged with 'v' prefix based on existing tags.

    Returns:
        "v" if versions use v-prefix, "" if they use bare numbers
    """
    try:
        # Get all tags sorted by version
        result = subprocess.run(
            ["git", "tag", "--sort=v:refname"],
            capture_output=True,
            text=True,
            check=True,
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


@handle_keyboard_interrupt()
def get_version(pyproject_path: Path) -> str:
    """Get current version from pyproject.toml."""
    content = pyproject_path.read_text()
    try:
        import tomllib

        data = tomllib.loads(content)

        if "project" in data and "version" in data["project"]:
            return data["project"]["version"]

        logger.error("Could not find version in pyproject.toml (project.version).")
        sys.exit(1)
    except tomllib.TOMLDecodeError:
        logger.error(
            "Invalid TOML format in pyproject.toml. Do you even know how to use a text editor?"
        )
        sys.exit(1)


def parse_version(version: str) -> tuple[int, int, int, BumpType | None, int | None]:
    """Parse version string into components.

    Args:
        version: Version string (e.g., "1.2.3", "1.2.3a1", "1.2.3.post1").

    Returns:
        Tuple of (major, minor, patch, pre-release type, pre-release number).
        Pre-release type is BumpType.DEV/ALPHA/BETA/RC/POST or None.
        Pre-release number can be None if no pre-release.
    """
    # Handle post suffix (.postN)
    if ".post" in version:
        version_part, post_num = version.rsplit(".post", 1)
        try:
            pre_num = int(post_num)
        except ValueError:
            logger.error("Invalid post-release number: %s", post_num)
            sys.exit(1)
        major, minor, patch = map(int, version_part.split("."))
        return major, minor, patch, BumpType.POST, pre_num

    # Handle dev suffix (.devN)
    if ".dev" in version:
        version_part, dev_num = version.rsplit(".dev", 1)
        try:
            pre_num = int(dev_num)
        except ValueError:
            logger.error("Invalid dev number: %s", dev_num)
            sys.exit(1)
        major, minor, patch = map(int, version_part.split("."))
        return major, minor, patch, BumpType.DEV, pre_num

    # Handle pre-release suffixes (aN, bN, rcN)
    suffix_map = {"a": BumpType.ALPHA, "b": BumpType.BETA, "rc": BumpType.RC}
    for suffix, bump_type in suffix_map.items():
        if suffix in version:
            version_part, pre_num = version.rsplit(suffix, 1)
            try:
                major, minor, patch = map(int, version_part.split("."))
                return major, minor, patch, bump_type, int(pre_num)
            except ValueError:
                logger.error("Invalid pre-release number: %s", pre_num)
                sys.exit(1)

    try:  # Parse version numbers
        major, minor, patch = map(int, version.split("."))
        return major, minor, patch, None, None
    except ValueError:
        logger.error("Invalid version format: %s. Numbers go left to right, champ.", version)
        sys.exit(1)


@handle_keyboard_interrupt()
def bump_version(bump_type: BumpType | str, current_version: str) -> str:
    """Calculate new version number based on bump type and current version.

    Args:
        bump_type: Version bump type (major/minor/patch/alpha/beta/rc) or specific version.
        current_version: Current version string.

    Returns:
        New version string.
    """
    if bump_type.count(".") >= 2:
        _handle_explicit_version(bump_type)
        return bump_type

    major, minor, patch, pre_type, pre_num = parse_version(current_version)
    return _get_base_version(bump_type, pre_type, major, minor, patch, pre_num)


def _get_base_version(
    bump_type: BumpType | str,
    pre_type: str | None,
    major: int,
    minor: int,
    patch: int,
    pre_num: int | None,
) -> str:
    """Calculate base version without dev suffix."""
    if bump_type.count(".") >= 2:
        return bump_type

    # Now we know it's a BumpType
    bump_type = BumpType(bump_type)  # Convert string to enum if it isn't already

    # Handle pre-release bumping
    if bump_type.is_prerelease or bump_type == BumpType.POST:
        return _handle_version_modifier(bump_type, pre_type, major, minor, patch, pre_num)

    # When moving from pre-release to release
    if pre_type and bump_type == BumpType.PATCH:
        return f"{major}.{minor}.{patch}"

    # Handle regular version bumping
    match bump_type:
        case BumpType.MAJOR:
            return f"{major + 1}.0.0"
        case BumpType.MINOR:
            return f"{major}.{minor + 1}.0"
        case BumpType.PATCH:
            return f"{major}.{minor}.{patch + 1}"
        case _:
            logger.error("Invalid bump type: %s", bump_type)
            sys.exit(1)


def _handle_explicit_version(version: str) -> None:
    """Validate explicit version number format.

    Raises:
        ValueError: If version number is invalid.
    """
    try:
        if "-" in version:
            version_part, _ = version.split("-", 1)
            major, minor, patch = map(int, version_part.split("."))
        else:
            major, minor, patch = map(int, version.split("."))
            if any(n < 0 for n in (major, minor, patch)):
                logger.error("Invalid version number: %s. Numbers cannot be negative.", version)
                sys.exit(1)
    except ValueError as e:
        if str(e).startswith("Invalid version number"):
            raise
        logger.error("Invalid format: %s. Must be three numbers separated by dots.", version)
        sys.exit(1)


def _handle_version_modifier(
    bump_type: BumpType | str,
    pre_type: BumpType | None,
    major: int,
    minor: int,
    patch: int,
    pre_num: int | None,
) -> str:
    """Calculate pre-release version bump.

    Handles progression through pre-release stages (alpha -> beta -> rc). Increments numbers within
    same pre-release type (alpha1 -> alpha2). Starts new pre-release series at 1 (1.2.3 -> 1.2.4a1).

    Args:
        bump_type: Target pre-release type (dev/alpha/beta/rc).
        pre_type: Current pre-release type (.dev/a/b/rc or None).
        major: Major version number.
        minor: Minor version number.
        patch: Patch version number.
        pre_num: Current pre-release number.

    Returns:
        New version string.
    """
    # Handle post-release versions first
    if bump_type == BumpType.POST:
        if pre_type == BumpType.POST and pre_num:
            return f"{major}.{minor}.{patch}.post{pre_num + 1}"
        if pre_type and pre_type.is_prerelease:
            logger.error(
                "Can't add post-release to %s%s, genius. "
                "How can you post-release something that isn't released? "
                "Finalize the version first.",
                pre_type,
                pre_num,
            )
            sys.exit(1)
        return f"{major}.{minor}.{patch}.post1"

    # Handle dev versions separately since they use dot notation
    if bump_type == BumpType.DEV:
        if pre_type == "dev" and pre_num:
            return f"{major}.{minor}.{patch}.dev{pre_num + 1}"
        return f"{major}.{minor}.{patch + 1}.dev1"

    # Map full names to version string components
    bump_type = BumpType(bump_type)
    new_suffix = bump_type.version_suffix

    # If we have an existing pre-release type, check progression
    if pre_type:
        if pre_type.sort_value() > bump_type.sort_value():
            logger.error(
                "Can't go backwards from %s to %s, idiot. Version progression is: dev -> alpha -> beta -> rc",
                pre_type.version_suffix,
                new_suffix,
            )
            sys.exit(1)

    # Handle incrementing same type
    if pre_num and pre_type == new_suffix:
        return f"{major}.{minor}.{patch}{new_suffix}{pre_num + 1}"

    # Starting new pre-release series (no previous pre-release)
    return f"{major}.{minor}.{patch + 1}{new_suffix}1"


@handle_keyboard_interrupt()
def update_version(
    bump_type: BumpType | str | None,
    commit_msg: str | None = None,
    tag_msg: str | None = None,
) -> None:
    """Update version, create git tag, and push changes.

    Args:
        bump_type: Version bump type (BumpType) or specific version string.
        commit_msg: Optional custom commit message.
        tag_msg: Optional tag annotation message.
    """
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        logger.error("No pyproject.toml found in current directory.")
        sys.exit(1)

    try:
        check_git_state()
        current_version = get_version(pyproject)
        new_version = bump_version(bump_type, current_version)

        # Update version
        if bump_type is not None:
            _update_version_in_pyproject(pyproject, new_version)
        handle_git_operations(new_version, bump_type, commit_msg, tag_msg, current_version)
        logger.info(
            "Successfully %s v%s!", "tagged" if bump_type is None else "updated to", new_version
        )

    except Exception as e:
        logger.error("Version update failed: %s", str(e))
        raise


def _update_version_in_pyproject(pyproject: Path, new_version: str) -> None:
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
        logger.error("Could not find version field in project section.")
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
        logger.error("Version update would create invalid TOML. Aborting.")
        sys.exit(1)

    # Write back the file
    pyproject.write_text(new_content)

    # Verify the changes
    if get_version(pyproject) != new_version:
        logger.error("Version update failed verification.")
        sys.exit(1)


@handle_keyboard_interrupt()
def cleanup_tags(old_version: str, new_version: str) -> None:
    """Remove all pre-release tags for relevant versions.

    Removes tags based on version bump type:
    - Major bump (1.x -> 2.x): Removes all 1.x pre-release tags
    - Minor bump (1.1 -> 1.2): Removes all 1.1.x pre-release tags
    - Patch bump (1.1.1 -> 1.1.2): Removes only 1.1.2 pre-release tags

    Args:
        old_version: Previous version string.
        new_version: New version string.
    """
    logger.debug(
        "Checking for pre-release tags to clean up when moving from %s to %s.",
        old_version,
        new_version,
    )

    patterns = _identify_tag_patterns(old_version, new_version)

    all_tags = set()
    for pattern in patterns:
        result = subprocess.run(
            ["git", "tag", "-l", pattern], capture_output=True, text=True, check=True
        )
        tags = result.stdout.strip().split("\n")
        if tags and tags[0]:  # Check if we actually found any tags
            all_tags.update(tags)

    if all_tags:
        logger.info("Cleaning up %d pre-release tags.", len(all_tags))
        _remove_found_tags(all_tags)


def _identify_tag_patterns(old_version: str, new_version: str) -> list[str]:
    """Find tag patterns to clean up based on version bump.

    Determines which pre-release tags should be cleaned up based on the type of version bump
    (major/minor/patch).

    Returns:
        List of glob patterns matching tags to be removed.
    """
    old_major, old_minor, _, _, _ = parse_version(old_version)
    new_major, new_minor, new_patch, _, _ = parse_version(new_version)

    version_prefix = detect_version_prefix()

    prerelease_patterns = [
        t.version_suffix + "*" for t in [BumpType.DEV, BumpType.ALPHA, BumpType.BETA, BumpType.RC]
    ]

    patterns = []
    if new_major > old_major:
        patterns.extend(
            f"{version_prefix}{old_major}.*{pattern}" for pattern in prerelease_patterns
        )
    elif new_minor > old_minor:
        patterns.extend(
            f"{version_prefix}{old_major}.{old_minor}.*{pattern}" for pattern in prerelease_patterns
        )
    else:
        patterns.extend(
            f"{version_prefix}{new_major}.{new_minor}.{new_patch}{pattern}"
            for pattern in prerelease_patterns
        )

    return patterns


@handle_keyboard_interrupt()
def _remove_found_tags(found_tags: set[str]) -> None:
    """Remove identified pre-release tags.

    Removes tags both locally and from remote if it exists. Remote tag deletion failures are ignored
    as tags might not exist remotely.

    Args:
        found_tags: Set of tag names to remove.
    """
    # Remove local tags
    for tag in found_tags:
        logger.info("Removing tag: %s", tag)
        subprocess.run(["git", "tag", "-d", tag], check=True)

    # Remove remote tags if remote exists
    remote_check = subprocess.run(["git", "remote"], capture_output=True, text=True, check=False)
    if remote_check.stdout.strip():
        logger.debug("Removing remote tags...")
        subprocess.run(
            ["git", "push", "--delete", "origin", *list(found_tags)],
            capture_output=True,
            check=False,
        )


@handle_keyboard_interrupt()
def handle_git_operations(
    new_version: str,
    bump_type: BumpType | str | None,
    commit_msg: str | None,
    tag_msg: str | None,
    current_version: str,
) -> None:
    """Handle git commit, tag, and push operations.

    1. Creates version bump commit if needed.
    2. Cleans up pre-release tags when finalizing version.
    3. Creates new version tag.
    4. Pushes changes and tags to remote.

    Args:
        new_version: The version string to tag with.
        bump_type: The type of version bump performed.
        commit_msg: An optional custom commit message.
        tag_msg: An optional tag annotation message.
        current_version: The previous version string.
    """
    version_prefix = detect_version_prefix()
    tag_name = f"{version_prefix}{new_version}"

    # Handle version bump commit if needed
    if bump_type is not None:
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        has_other_changes = any(
            not line.endswith("pyproject.toml") for line in result.stdout.splitlines()
        )

        # Stage only pyproject.toml
        subprocess.run(["git", "add", "pyproject.toml"], check=True)

        if commit_msg:
            msg = f"{commit_msg}\n\nBump version to {new_version}"
        else:
            msg = f"Bump version to {new_version}"

        subprocess.run(["git", "commit", "-m", msg], check=True)

        if has_other_changes:
            logger.info(
                "Committed pyproject.toml with the version bump. "
                "Other changes in the working directory were skipped and preserved."
            )

    # Clean up pre-release tags when moving to a release version
    if isinstance(bump_type, BumpType):
        _, _, _, pre_type, _ = parse_version(new_version)
        if not pre_type:  # If new version is a release version
            cleanup_tags(current_version, new_version)
    elif bump_type and bump_type.count(".") >= 2:  # explicit version
        if not any(
            t.version_suffix in bump_type
            for t in [BumpType.DEV, BumpType.ALPHA, BumpType.BETA, BumpType.RC]
        ):
            cleanup_tags(current_version, new_version)

    # Check if tag already exists
    if (
        subprocess.run(["git", "rev-parse", tag_name], capture_output=True, check=False).returncode
        == 0
    ):
        logger.error("Tag %s already exists.", tag_name)
        sys.exit(1)

    # Create tag and push
    if tag_msg:
        subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_msg], check=True)
    else:
        subprocess.run(["git", "tag", tag_name], check=True)

    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "push", "--tags"], check=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Version management tool")
    parser.add_argument(
        "type",
        nargs="?",
        default=BumpType.PATCH,
        choices=[t.value for t in BumpType],
        help="version bump type: major, minor, patch, dev, alpha, beta, rc, post, or x.y.z",
    )
    parser.add_argument(
        "-m",
        "--message",
        help="custom commit message (default: 'Bump version to x.y.z')",
    )
    parser.add_argument(
        "-t",
        "--tag-message",
        help="custom tag annotation message",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="show what the new version would be without making changes",
    )
    return parser.parse_args()


@handle_keyboard_interrupt()
def main() -> None:
    """Perform version bump."""
    args = parse_args()

    try:
        # Convert to enum if it's not an explicit version
        bump_type = args.type if args.type.count(".") >= 2 else BumpType(args.type)

        if args.preview:
            pyproject = Path("pyproject.toml")
            if not pyproject.exists():
                logger.error("No pyproject.toml found in current directory.")
                sys.exit(1)

            current_version = get_version(pyproject)
            new_version = bump_version(bump_type, current_version)

            logger.info("Current version: %s", current_version)
            logger.info("Would bump to:   %s", new_version)
        else:
            update_version(bump_type=args.type, commit_msg=args.message, tag_msg=args.tag_message)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
