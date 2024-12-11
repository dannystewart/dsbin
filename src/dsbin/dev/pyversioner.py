from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, get_args

from dsutil import configure_traceback
from dsutil.env import DSEnv
from dsutil.log import LocalLogger
from dsutil.shell import confirm_action, handle_keyboard_interrupt

if TYPE_CHECKING:
    from collections.abc import Sequence

configure_traceback()

env = DSEnv("pyversioner")
env.add_debug_var()

log_level = "debug" if env.debug else "info"
logger = LocalLogger.setup_logger(level=log_level, message_only=not env.debug)

BumpType = Literal["major", "minor", "patch", "dev", "alpha", "beta", "rc"]


@handle_keyboard_interrupt()
def dsbump() -> None:
    """Entry point for dsbump command."""
    bump_command(sys.argv[1:] if len(sys.argv) > 1 else None)


@handle_keyboard_interrupt()
def dspause() -> None:
    """Entry point for dspause command."""
    args = sys.argv[1:] if len(sys.argv) > 1 else ["patch"]
    pause_command(args)


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
        ["git", "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error("Not on a git branch (detached HEAD state).")
        sys.exit(1)


@handle_keyboard_interrupt()
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
        except KeyError:
            logger.error("Could not find version in pyproject.toml.")
            sys.exit(1)


def parse_version(version: str) -> tuple[int, int, int, str | None, int | None]:
    """Parse version string into components."""
    # Handle dev suffix (.devN)
    if ".dev" in version:
        version_part, dev_num = version.rsplit(".dev", 1)
        try:
            pre_num = int(dev_num)
        except ValueError:
            logger.error("Invalid dev number: %s", dev_num)
            sys.exit(1)
        pre_type = "dev"
    # Handle pre-release suffixes (aN, bN, rcN)
    elif any(x in version for x in ("a", "b", "rc")):
        for pre in ("a", "b", "rc"):
            if pre in version:
                version_part, pre_num = version.rsplit(pre, 1)
                try:
                    pre_num = int(pre_num)
                except ValueError:
                    logger.error("Invalid pre-release number: %s", pre_num)
                    sys.exit(1)
                pre_type = pre
                break
    else:
        version_part = version
        pre_type = None
        pre_num = None

    try:  # Parse version numbers
        major, minor, patch = map(int, version_part.split("."))
        return major, minor, patch, pre_type, pre_num
    except ValueError:
        logger.error("Invalid version format: %s", version)
        sys.exit(1)


@handle_keyboard_interrupt()
def bump_version(bump_type: BumpType | str | None, current_version: str) -> str:
    """Calculate new version number."""
    if bump_type is None:
        return current_version

    # Handle explicit version setting
    if bump_type.count(".") >= 2:
        _handle_explicit_version(bump_type)
        return bump_type

    # Parse current version
    major, minor, patch, pre_type, pre_num = parse_version(current_version)

    # Handle dev version bumping
    if bump_type == "dev":
        return _handle_dev_version(pre_type, major, minor, patch, pre_num)

    # Handle pre-release bumping
    if bump_type in ("alpha", "beta", "rc"):
        return _handle_pre_version(bump_type, pre_type, major, minor, patch, pre_num)

    # When moving from pre-release to release
    if pre_type in ("a", "b", "rc") and bump_type == "patch":
        return f"{major}.{minor}.{patch}"

    # Handle regular version bumping
    match bump_type:
        case "major":
            return f"{major + 1}.0.0"
        case "minor":
            return f"{major}.{minor + 1}.0"
        case "patch":
            return f"{major}.{minor}.{patch + 1}"
        case _:
            logger.error("Invalid bump type: %s", bump_type)
            sys.exit(1)


def _handle_explicit_version(version: str) -> None:
    """Validate explicit version number format."""
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


def _handle_dev_version(
    pre_type: str, major: int, minor: int, patch: int, pre_num: int | None
) -> str:
    """Calculate dev version bump."""
    if pre_type == "dev":
        # Increment dev number
        return f"{major}.{minor}.{patch}.dev{pre_num + 1 if pre_num else 1}"
    # Start dev series for next patch version
    return f"{major}.{minor}.{patch + 1}.dev1"


def _handle_pre_version(
    bump_type: BumpType | str,
    pre_type: str,
    major: int,
    minor: int,
    patch: int,
    pre_num: int | None,
) -> str:
    """Calculate pre-release version bump."""
    pre_map = {"alpha": "a", "beta": "b", "rc": "rc"}
    new_pre = pre_map[bump_type]

    if pre_type == new_pre:
        # Increment existing pre-release
        return f"{major}.{minor}.{patch}{new_pre}{pre_num + 1 if pre_num else 1}"
    if pre_type in ("a", "b", "rc"):
        # Moving to next pre-release type
        if _pre_release_order(new_pre) > _pre_release_order(pre_type):
            return f"{major}.{minor}.{patch}{new_pre}1"
        # Moving backwards not allowed
        logger.error("Cannot move from %s to %s.", pre_type, new_pre)
        sys.exit(1)
    # Start new pre-release series
    return f"{major}.{minor}.{patch + 1}{new_pre}1"


def _pre_release_order(pre_type: str) -> int:
    """Get sort order for pre-release types."""
    order = {"a": 0, "b": 1, "rc": 2}
    return order.get(pre_type, -1)


@handle_keyboard_interrupt()
def update_version(
    bump_type: BumpType | str | None,
    commit_msg: str | None = None,
    tag_msg: str | None = None,
    stash: bool = False,
    drop_commits: bool = False,
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

        # If dropping commits is requested and we're moving from dev to release
        if (
            drop_commits
            and (".dev" in current_version or any(x in current_version for x in ("a", "b", "rc")))
            and not any(x in new_version for x in (".dev", "a", "b", "rc"))
        ):
            safe_to_drop, commits = _check_pre_commits_safe_to_drop()
            if not safe_to_drop:
                logger.error("Cannot safely drop dev commits without conflicts. Aborting.")
                sys.exit(1)
            if commits and confirm_action(
                "Are you sure you want to drop these commits and force push?",
                default_to_yes=False,
                prompt_color="yellow",
            ):
                _drop_pre_commits(commits)

        # Stash if needed, getting stash hash for safety
        stashed, stash_hash = handle_stash(stash)

        try:  # Update version if needed
            if bump_type is not None:
                _update_version_in_pyproject(pyproject, bump_type, new_version)
            _handle_git_operations(new_version, bump_type, commit_msg, tag_msg, current_version)
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


@handle_keyboard_interrupt()
def _update_version_in_pyproject(
    pyproject: Path, bump_type: BumpType | str, new_version: str
) -> None:
    """Update version in pyproject.toml using Poetry or manual update."""
    if bump_type == "dev" or ".dev" in new_version:  # Set dev versions manually for Poetry
        logger.debug("Using manual update for dev version.")
        content = pyproject.read_text()
        import tomllib

        data = tomllib.loads(content)
        data["tool"]["poetry"]["version"] = new_version
        import tomli_w

        pyproject.write_text(tomli_w.dumps(data))

    else:  # Try Poetry for regular versions
        try:
            subprocess.run(["poetry", "version", bump_type], check=True)

        # Fall back to manual version update if Poetry fails
        except subprocess.CalledProcessError:
            logger.debug("Poetry version update failed, falling back to manual update.")
            content = pyproject.read_text()
            import tomllib

            data = tomllib.loads(content)
            data["tool"]["poetry"]["version"] = new_version
            import tomli_w

            pyproject.write_text(tomli_w.dumps(data))

    # Verify the changes
    if get_version(pyproject) != new_version:
        logger.error("Version update failed verification.")
        sys.exit(1)


@handle_keyboard_interrupt()
def _cleanup_pre_tags(old_version: str, new_version: str) -> None:
    """Remove all pre-release tags for relevant versions."""
    logger.debug(
        "Checking for dev tags to clean up when moving from %s to %s.", old_version, new_version
    )

    old_major, old_minor, _, _, _ = parse_version(old_version)
    new_major, new_minor, new_patch, _, _ = parse_version(new_version)

    patterns = []
    if new_major > old_major:  # Major bump: clean all pre-release tags
        patterns.extend(
            [
                f"v{old_major}.*.dev*",
                f"v{old_major}.*a*",
                f"v{old_major}.*b*",
                f"v{old_major}.*rc*",
            ]
        )
    elif new_minor > old_minor:  # Minor bump: clean minor pre-releases
        patterns.extend(
            [
                f"v{old_major}.{old_minor}.*.dev*",
                f"v{old_major}.{old_minor}.*a*",
                f"v{old_major}.{old_minor}.*b*",
                f"v{old_major}.{old_minor}.*rc*",
            ]
        )
    else:  # Patch bump or explicit version
        patterns.extend(
            [
                f"v{new_major}.{new_minor}.{new_patch}.dev*",
                f"v{new_major}.{new_minor}.{new_patch}a*",
                f"v{new_major}.{new_minor}.{new_patch}b*",
                f"v{new_major}.{new_minor}.{new_patch}rc*",
            ]
        )

    all_dev_tags = set()
    for pattern in patterns:
        result = subprocess.run(
            ["git", "tag", "-l", pattern], capture_output=True, text=True, check=True
        )
        tags = result.stdout.strip().split("\n")
        if tags and tags[0]:  # Check if we actually found any tags
            all_dev_tags.update(tags)

    if all_dev_tags:
        logger.info("Cleaning up %d dev tags.", len(all_dev_tags))

        # Remove local tags
        for tag in all_dev_tags:
            logger.info("Removing tag: %s", tag)
            subprocess.run(["git", "tag", "-d", tag], check=True)

        # Remove remote tags if remote exists
        remote_check = subprocess.run(["git", "remote"], capture_output=True, text=True)
        if remote_check.stdout.strip():
            logger.debug("Removing remote tags...")

            # Delete all matching remote tags in one command
            subprocess.run(
                ["git", "push", "--delete", "origin"] + list(all_dev_tags),
                capture_output=True,  # Suppress output in case tags don't exist remotely
                check=False,  # Don't fail if some tags don't exist remotely
            )


def _check_pre_commits_safe_to_drop() -> tuple[bool, list[str]]:
    """Check if pre-release commits can be safely dropped."""
    logger.debug("Checking if pre-release commits can be safely dropped.")

    # Find first pre-release tag of current series
    current_version = get_version(Path("pyproject.toml"))
    major, minor, patch, _, _ = parse_version(current_version)
    base_version = f"v{major}.{minor}.{patch}"

    result = subprocess.run(
        ["git", "tag", "--sort=v:refname"], capture_output=True, text=True, check=True
    )
    first_dev = next(
        (tag for tag in result.stdout.strip().split("\n") if tag.startswith(f"{base_version}.dev")),
        None,
    )

    if not first_dev:
        logger.error("No dev tags found for current version series.")
        return False, []

    # Check what files would be affected
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{first_dev}^", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    changed_files = set(result.stdout.strip().split("\n"))

    # If anything other than pyproject.toml is changed, abort
    if changed_files - {"pyproject.toml"}:
        logger.error("Cannot safely drop commits as it would affect the following files:")
        for file in sorted(changed_files - {"pyproject.toml"}):
            logger.error("  %s", file)
        return False, []

    # Get commits that would be dropped
    result = subprocess.run(
        ["git", "log", "--oneline", f"{first_dev}..HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    dev_commits = [line.split()[0] for line in result.stdout.strip().split("\n") if line]

    if dev_commits:
        logger.info("Found %d commits to drop:", len(dev_commits))
        for commit in result.stdout.strip().split("\n"):
            if commit:
                logger.info("  %s", commit)

    return True, dev_commits


def _drop_pre_commits(commits: list[str]) -> None:
    """Drop pre-release commits by removing them from history via interactive rebase."""
    # Create rebase script to drop each commit
    script = "".join(f"drop {commit}\n" for commit in commits)
    logger.debug("Rebase script:\n%s", script)

    # Use interactive rebase
    process = subprocess.Popen(
        ["git", "rebase", "-i", f"HEAD~{len(commits)}"], stdin=subprocess.PIPE, text=True
    )
    process.communicate(input=script)
    if process.returncode != 0:
        logger.error("Rebase failed.")
        sys.exit(1)

    # Force push the rewritten history
    logger.warning("Force pushing changes - this will rewrite history!")
    subprocess.run(["git", "push", "--force"], check=True)


@handle_keyboard_interrupt()
def _handle_git_operations(
    new_version: str,
    bump_type: BumpType | str | None,
    commit_msg: str | None,
    tag_msg: str | None,
    current_version: str,
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

    # Clean up pre-release tags when moving to a release version
    if (
        bump_type in get_args(BumpType)
        and not any(x in new_version for x in (".dev", "a", "b", "rc"))
    ) or (
        bump_type
        and bump_type.count(".") >= 2
        and not any(x in bump_type for x in (".dev", "a", "b", "rc"))
    ):
        _cleanup_pre_tags(current_version, new_version)

    # Check if tag already exists
    if subprocess.run(["git", "rev-parse", tag_name], capture_output=True).returncode == 0:
        logger.error("Tag %s already exists.", tag_name)
        sys.exit(1)

    # Create tag and push
    if tag_msg:
        subprocess.run(["git", "tag", "-a", tag_name, "-m", tag_msg], check=True)
    else:
        subprocess.run(["git", "tag", tag_name], check=True)

    subprocess.run(["git", "push"], check=True)
    subprocess.run(["git", "push", "--tags"], check=True)


@handle_keyboard_interrupt()
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


def bump_command(
    args: Sequence[str] | None = None,
    bump_type: BumpType | str = "patch",
    commit_msg: str | None = None,
    tag_msg: str | None = None,
    drop_commits: bool = False,
) -> None:
    """Bump version, commit, tag, and push."""
    if args is not None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--drop-commits",
            action="store_true",
            help="drop dev commits when finalizing version (dangerous!)",
        )

        # Parse out any flags then handle positional args
        known_args, remaining_args = parser.parse_known_args(args)
        parsed_type = "patch"  # Default
        parsed_commit_msg = None  # First non-version arg is commit message
        parsed_tag_msg = None

        if remaining_args:  # First arg could be type or commit message
            if remaining_args[0] in get_args(BumpType) or remaining_args[0].count(".") >= 2:
                parsed_type = remaining_args[0]
                if len(remaining_args) > 1:
                    parsed_commit_msg = remaining_args[1]
                    if len(remaining_args) > 2:
                        parsed_tag_msg = remaining_args[2]
            else:  # First arg is commit message
                parsed_commit_msg = remaining_args[0]
                if len(remaining_args) > 1:
                    parsed_tag_msg = remaining_args[1]

        bump_type = parsed_type
        commit_msg = parsed_commit_msg
        tag_msg = parsed_tag_msg
        drop_commits = known_args.drop_commits

    update_version(bump_type, commit_msg, tag_msg, drop_commits=drop_commits)


@handle_keyboard_interrupt()
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

        if args:  # First arg could be type or commit message
            if args[0] in get_args(BumpType) or args[0].count(".") == 2:
                parsed_type = args[0]
                if len(args) > 1:
                    parsed_commit_msg = args[1]
                    if len(args) > 2:
                        parsed_tag_msg = args[2]
            else:  # First arg is commit message
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
        help="version bump type (major/minor/patch or specific version)",
    )
    bump_parser.add_argument("-m", "--message", help="Commit message")
    bump_parser.add_argument("-t", "--tag-message", help="Tag message")
    bump_parser.add_argument(
        "--drop-commits",
        action="store_true",
        help="drop dev commits when finalizing version (dangerous!)",
    )

    # pause command
    pause_parser = subparsers.add_parser(
        "pause", help="Stash changes, bump version, then restore changes"
    )
    pause_parser.add_argument(
        "type",
        nargs="?",
        default="patch",
        help="version bump type (major/minor/patch or specific version)",
    )
    pause_parser.add_argument("-m", "--message", help="Commit message")
    pause_parser.add_argument("-t", "--tag-message", help="Tag message")

    return parser.parse_args()


@handle_keyboard_interrupt()
def main() -> None:
    """Perform version update operations."""
    try:
        args = parse_args()
        match args.command:
            case "bump":
                bump_command(
                    bump_type=args.type,
                    commit_msg=args.message,
                    tag_msg=args.tag_message,
                    drop_commits=args.drop_commits,
                )
            case "pause":
                pause_command(
                    bump_type=args.type, commit_msg=args.message, tag_msg=args.tag_message
                )
            case _:
                msg = f"Invalid command: {args.command}"
                raise ValueError(msg)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
