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


def script_bump() -> None:
    """Entry point for dsbump command."""
    cmd_bump(sys.argv[1:] if len(sys.argv) > 1 else None)


def script_tag() -> None:
    """Entry point for dstag command."""
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    cmd_tag(args)


def script_pause() -> None:
    """Entry point for dspause command."""
    # If no args provided, use default "patch"
    args = sys.argv[1:] if len(sys.argv) > 1 else ["patch"]
    cmd_pause(args)


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
        return bump_type

    major, minor, patch = map(int, current_version.split("."))

    match bump_type:
        case "major":
            return f"{major + 1}.0.0"
        case "minor":
            return f"{major}.{minor + 1}.0"
        case "patch":
            return f"{major}.{minor}.{patch + 1}"
        case _:
            msg = f"Invalid bump type: {bump_type}"
            raise ValueError(msg)


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

    current_version = get_version(pyproject)
    new_version = bump_version(bump_type, current_version)

    # Stash if needed
    if stash and subprocess.run(["git", "diff", "--quiet"], capture_output=True).returncode != 0:
        logger.info("Stashing changes...")
        subprocess.run(["git", "stash", "push", "-m", "temporary stash for version bump"])
        stashed = True
    else:
        stashed = False

    try:
        # Update version only if we're bumping
        if bump_type is not None:
            try:
                # Try Poetry first
                subprocess.run(["poetry", "version", bump_type], check=True)
            except subprocess.CalledProcessError:
                # Fallback to manual file editing
                content = pyproject.read_text()
                import tomllib

                data = tomllib.loads(content)

                # Update version in data
                data["tool"]["poetry"]["version"] = new_version

                # Write back to file
                import tomli_w

                pyproject.write_text(tomli_w.dumps(data))

            subprocess.run(["git", "add", "pyproject.toml"], check=True)

            if commit_msg:
                msg = f"{commit_msg}\n\nBump version to {new_version}"
            else:
                msg = f"Bump version to {new_version}"

            subprocess.run(["git", "commit", "-m", msg], check=True)

        # Tag operation happens regardless of bump
        if tag_msg:
            subprocess.run(["git", "tag", "-a", f"v{new_version}", "-m", tag_msg], check=True)
        else:
            subprocess.run(["git", "tag", f"v{new_version}"], check=True)

        subprocess.run(["git", "push"], check=True)
        subprocess.run(["git", "push", "--tags"], check=True)

        logger.info(
            "Successfully %s v%s!", "tagged" if bump_type is None else "updated to", new_version
        )

    finally:
        if stashed:
            logger.info("Restoring stashed changes...")
            subprocess.run(["git", "stash", "pop"])


def cmd_bump(
    args: Sequence[str] | None = None,
    bump_type: BumpType | str = "patch",
    commit_msg: str | None = None,
    tag_msg: str | None = None,
) -> None:
    """Bump version, commit, tag, and push."""
    if args is not None:
        parsed_type = "patch"  # default
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


def cmd_tag(
    args: Sequence[str] | None = None,
    tag_msg: str | None = None,
) -> None:
    """Tag current version and push."""
    if args is not None:
        parsed_tag_msg = None if len(args) == 0 else args[0]
        tag_msg = parsed_tag_msg

    update_version(None, tag_msg=tag_msg)


def cmd_pause(
    args: Sequence[str] | None = None,
    bump_type: BumpType | str = "patch",
    commit_msg: str | None = None,
    tag_msg: str | None = None,
) -> None:
    """Stash changes, bump version, then restore changes."""
    if args is not None:
        # Match same behavior as cmd_bump
        parsed_type = "patch"  # default
        parsed_commit_msg = None
        parsed_tag_msg = None

        if args:
            # First arg could be type or commit msg
            if args[0] in ("major", "minor", "patch") or args[0].count(".") == 2:
                parsed_type = args[0]
                if len(args) > 1:
                    parsed_commit_msg = args[1]
                    if len(args) > 2:
                        parsed_tag_msg = args[2]
            else:
                # First arg is commit msg
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
            cmd_bump(bump_type=args.type, commit_msg=args.message, tag_msg=args.tag_message)
        case "tag":
            cmd_tag(tag_msg=args.message)
        case "pause":
            cmd_pause(bump_type=args.type, commit_msg=args.message, tag_msg=args.tag_message)
        case _:
            msg = f"Invalid command: {args.command}"
            raise ValueError(msg)


if __name__ == "__main__":
    main()
