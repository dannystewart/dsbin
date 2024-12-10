from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from dsutil.log import LocalLogger

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = LocalLogger.setup_logger("versioner")

BumpType = Literal["major", "minor", "patch"]


def dsbump() -> None:
    """Entry point for dsbump command."""
    bump_command(sys.argv[1:] if len(sys.argv) > 1 else None)


def dstag() -> None:
    """Entry point for dstag command."""
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    tag_command(args)


def dspause() -> None:
    """Entry point for dspause command."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ["patch"]
    pause_command(args)


def get_version(pyproject_path: Path) -> str:
    """Get current version from pyproject.toml."""
    try:
        result = subprocess.run(
            ["poetry", "version", "-s"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        content = pyproject_path.read_text()  # Fallback to reading file directly
        import tomllib

        data = tomllib.loads(content)
        try:
            return data["tool"]["poetry"]["version"]
        except KeyError as e:
            msg = "Could not find version in pyproject.toml."
            raise ValueError(msg) from e


def bump_version(bump_type: BumpType | str | None, current_version: str) -> str:
    """Calculate new version number."""
    if bump_type is None:
        return current_version

    if bump_type.count(".") == 2:
        try:
            major, minor, patch = map(int, bump_type.split("."))
            if any(n < 0 for n in (major, minor, patch)):
                msg = f"Invalid version number: {bump_type}. Numbers cannot be negative."
                raise ValueError(msg)
            return bump_type
        except ValueError as e:
            if str(e).startswith("Invalid version number"):
                raise
            msg = f"Invalid version format: {bump_type}. Must be three numbers separated by dots."
            raise ValueError(msg) from e

    return current_version


def update_version(
    bump_type: BumpType | str | None,
    commit_msg: str | None = None,
    tag_msg: str | None = None,
    stash: bool = False,
) -> None:
    """Main version update function."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        logger.error("No pyproject.toml found in current directory.")
        return

    try:  # Verify git state before we do anything
        check_git_state()
        current_version = get_version(pyproject)
        new_version = bump_version(bump_type, current_version)

        # Stash if needed, getting stash hash for safety
        stashed, stash_hash = handle_stash(stash)

        try:  # Update version if needed
            if bump_type is not None:
                _update_version_in_pyproject(pyproject, bump_type, new_version)
            _handle_git_operations(new_version, bump_type, commit_msg, tag_msg)
            logger.info(
                "Successfully %s v%s!", "tagged" if bump_type is None else "updated to", new_version
            )
        except Exception:
            if stashed:  # If anything goes wrong, make sure to restore stash
                logger.warning("Operation failed. Attempting to restore stashed changes...")
                if stash_hash:  # Apply specific stash by hash to avoid conflicts
                    subprocess.run(["git", "stash", "apply", stash_hash], check=True)
                    subprocess.run(["git", "stash", "drop", stash_hash], check=True)
                else:  # Fallback to pop if we somehow lost track of the hash
                    subprocess.run(["git", "stash", "pop"], check=True)
            raise

    except Exception as e:
        logger.error("Version update failed: %s", str(e))
        raise


def check_git_state() -> None:
    """Check if we're in a git repository and on a valid branch."""
    try:  # Check if we're in a git repo
        subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        msg = "Not a git repository."
        raise RuntimeError(msg) from e

    # Check if we're on a branch (not in detached HEAD state)
    result = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True
    )
    if result.returncode != 0:
        msg = "Not on a git branch (detached HEAD state)."
        raise RuntimeError(msg)


def handle_stash(stash: bool) -> tuple[bool, str | None]:
    """Handle stashing of changes, return if stashed and stash hash."""
    if not stash:
        return False, None

    # Check if there are changes to stash
    result = subprocess.run(["git", "diff", "--quiet"], capture_output=True)
    if result.returncode == 0:
        return False, None

    before = subprocess.run(  # Get current stash list for comparison
        ["git", "rev-list", "-g", "stash"], capture_output=True, text=True
    ).stdout.split()

    # Stash changes
    subprocess.run(["git", "stash", "push", "-m", "Temporary stash for version bump"], check=True)

    after = subprocess.run(  # Get new stash list to find our stash
        ["git", "rev-list", "-g", "stash"], capture_output=True, text=True
    ).stdout.split()

    # Find the new stash hash
    stash_hash = next((h for h in after if h not in before), None)
    return True, stash_hash


def _update_version_in_pyproject(
    pyproject: Path, bump_type: BumpType | str, new_version: str
) -> None:
    """Update version in pyproject.toml using Poetry or manual update."""
    try:  # Try Poetry first
        subprocess.run(["poetry", "version", bump_type], check=True)
    except subprocess.CalledProcessError:
        logger.debug("Poetry version update failed, falling back to manual update.")
        content = pyproject.read_text()  # Fallback to manual file editing
        import tomllib

        data = tomllib.loads(content)
        data["tool"]["poetry"]["version"] = new_version
        import tomli_w

        pyproject.write_text(tomli_w.dumps(data))

    # Verify the changes
    if get_version(pyproject) != new_version:
        msg = "Version update failed verification"
        raise RuntimeError(msg)


def _handle_git_operations(
    new_version: str,
    bump_type: BumpType | str | None,
    commit_msg: str | None,
    tag_msg: str | None,
) -> None:
    """Handle git commit, tag, and push operations."""
    tag_name = f"v{new_version}"

    # Handle version bump commit if needed
    if bump_type is not None:
        subprocess.run(["git", "add", "pyproject.toml"], check=True)

        if commit_msg:
            msg = f"{commit_msg}\n\nBump version to {new_version}"
        else:
            msg = f"Bump version to {new_version}"

        subprocess.run(["git", "commit", "-m", msg], check=True)

    # Check if tag already exists
    if subprocess.run(["git", "rev-parse", tag_name], capture_output=True).returncode == 0:
        msg = f"Tag {tag_name} already exists"
        raise RuntimeError(msg)

    # Create tag and push
    if tag_msg:
        subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_msg], check=True)
    else:
        subprocess.run(["git", "tag", tag_name], check=True)

    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "push", "--tags"], check=True)


def bump_command(
    args: Sequence[str] | None = None,
    bump_type: BumpType | str = "patch",
    commit_msg: str | None = None,
    tag_msg: str | None = None,
) -> None:
    """Bump version, commit, tag, and push."""
    if args is not None:
        parsed_type = "patch"  # Default
        parsed_commit_msg = None  # First non-version arg is commit msg
        parsed_tag_msg = None

        if args:  # First arg could be type or commit msg
            if args[0] in ("major", "minor", "patch") or args[0].count(".") == 2:
                parsed_type = args[0]
                if len(args) > 1:
                    parsed_commit_msg = args[1]
                    if len(args) > 2:
                        parsed_tag_msg = args[2]
            else:  # First arg is commit msg
                parsed_commit_msg = args[0]
                if len(args) > 1:
                    parsed_tag_msg = args[1]

        bump_type = parsed_type
        commit_msg = parsed_commit_msg
        tag_msg = parsed_tag_msg

    update_version(bump_type, commit_msg, tag_msg)


def tag_command(
    args: Sequence[str] | None = None,
    tag_msg: str | None = None,
) -> None:
    """Tag current version and push."""
    if args is not None:
        parsed_tag_msg = None if len(args) == 0 else args[0]
        tag_msg = parsed_tag_msg

    update_version(None, tag_msg=tag_msg)


def pause_command(
    args: Sequence[str] | None = None,
    bump_type: BumpType | str = "patch",
    commit_msg: str | None = None,
    tag_msg: str | None = None,
) -> None:
    """Stash changes, bump version, then restore changes."""
    if args is not None:
        parsed_type = "patch"  # Default
        parsed_commit_msg = None
        parsed_tag_msg = None

        if args:  # First arg could be type or commit msg
            if args[0] in ("major", "minor", "patch") or args[0].count(".") == 2:
                parsed_type = args[0]
                if len(args) > 1:
                    parsed_commit_msg = args[1]
                    if len(args) > 2:
                        parsed_tag_msg = args[2]
            else:  # First arg is commit msg
                parsed_commit_msg = args[0]
                if len(args) > 1:
                    parsed_tag_msg = args[1]

        bump_type = parsed_type
        commit_msg = parsed_commit_msg
        tag_msg = parsed_tag_msg

    update_version(bump_type, commit_msg, tag_msg, stash=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Version management tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # bump command
    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument(
        "type",
        nargs="?",
        default="patch",
        help="Version bump type (major/minor/patch or specific version)",
    )
    bump_parser.add_argument("-m", "--message", help="Commit message")
    bump_parser.add_argument("-t", "--tag-message", help="Tag message")

    # tag command
    tag_parser = subparsers.add_parser("tag", help="Tag current version")
    tag_parser.add_argument("-m", "--message", help="Tag message")

    # pause command
    pause_parser = subparsers.add_parser(
        "pause", help="Stash changes, bump version, then restore changes"
    )
    pause_parser.add_argument(
        "type",
        nargs="?",
        default="patch",
        help="Version bump type (major/minor/patch or specific version)",
    )
    pause_parser.add_argument("-m", "--message", help="Commit message")
    pause_parser.add_argument("-t", "--tag-message", help="Tag message")

    return parser.parse_args()


def main() -> None:
    """Perform version update operations."""
    args = parse_args()

    match args.command:
        case "bump":
            bump_command(bump_type=args.type, commit_msg=args.message, tag_msg=args.tag_message)
        case "tag":
            tag_command(tag_msg=args.message)
        case "pause":
            pause_command(bump_type=args.type, commit_msg=args.message, tag_msg=args.tag_message)
        case _:
            msg = f"Invalid command: {args.command}"
            raise ValueError(msg)


if __name__ == "__main__":
    main()
