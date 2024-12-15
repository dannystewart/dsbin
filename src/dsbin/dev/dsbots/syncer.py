from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

from dsutil.animation import start_animation, stop_animation
from dsutil.diff import show_diff
from dsutil.log import LocalLogger
from dsutil.shell import confirm_action, handle_keyboard_interrupt

logger = LocalLogger.setup_logger(__name__)

# Root directories
PROD_ROOT = Path("/home/danny/docker/dsbots")
DEV_ROOT = Path("/home/danny/docker/dsbots-dev")

# Directories to sync entirely
SYNC_DIRS = [
    "config",  # All configs including private
    "data",  # All shared resources
]

# Individual files
SYNC_FILES = [
    "src/dsbots/config/ip_whitelist.py",
    "src/dsbots/.env",
]

# Files and directories to exclude
# Will match recursively, so "logs/" will exclude all logs directories
EXCLUDE_PATTERNS = [
    "__pycache__/",
    ".git/",
    "cache/",
    "gifs/",
    "logs/",
    "temp/",
    "tmp/",
    "*.pyc",
    ".gitignore",
    "inactive_bots.yaml",
]


def should_exclude(path: Path) -> bool:
    """Check if a path should be excluded based on patterns. Handles both file patterns (*.pyc)
    and directory patterns (logs/). Directory patterns should end with a forward slash and will
    match directories recursively, so "logs/" will exclude all logs directories regardless of depth.
    """
    name = str(path)
    if path.is_dir():
        name = f"{name}/"
    return any(
        (pattern.endswith("/") and pattern in f"{name}/")
        or (not pattern.endswith("/") and path.match(pattern))
        for pattern in EXCLUDE_PATTERNS
    )


@handle_keyboard_interrupt(message="Sync interrupted by user.", use_logging=True)
def sync_file(source: Path, target: Path) -> bool:
    """Sync a single file, showing diff if text file."""
    if not source.exists():
        logger.warning("Source file does not exist: %s", source)
        return False

    # New file
    if not target.exists():
        logger.warning("New file: %s", source.name)
        logger.info("  Source: %s", source)
        logger.info("  Size: %s bytes", source.stat().st_size)
        if confirm_action("Create new file?", prompt_color="yellow"):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return True
        return False

    # Existing file
    if filecmp.cmp(source, target, shallow=False):
        return False

    try:  # Try to treat as text file
        current = target.read_text()
        new = source.read_text()
        result = show_diff(current, new, target.name)

        # Show summary instead of full diff for new/deleted files
        if not current:  # New file
            logger.warning("File will be created: %s", target.name)
            logger.info("  Lines: %d", len(new.splitlines()))
        elif not new:  # Deleted file
            logger.warning("File will be deleted: %s", target.name)
            logger.info("  Current lines: %d", len(current.splitlines()))
        else:  # Modified file
            logger.info("Changes: +%d -%d lines", len(result.additions), len(result.deletions))

    except UnicodeDecodeError:  # Binary file
        logger.warning("Binary file detected: %s", target.name)
        logger.info("  Source: %s", source)
        logger.info("  Target: %s", target)
        logger.info("  Size: %s -> %s bytes", target.stat().st_size, source.stat().st_size)

    if confirm_action(f"Update {target.name}?", prompt_color="yellow"):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return True

    return False


@handle_keyboard_interrupt(message="Sync interrupted by user.", use_logging=True)
def sync_directory(source_dir: Path, target_dir: Path) -> list[str]:
    """Sync a directory, returning list of changed files."""
    changed_files = []

    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    animation_thread = start_animation(f"Syncing {source_dir.name}...", "blue")

    try:
        for source_path in source_dir.rglob("*"):
            if should_exclude(source_path):
                continue

            # Get the relative path and construct target path
            rel_path = source_path.relative_to(source_dir)
            target_path = target_dir / rel_path

            if source_path.is_file() and (
                not target_path.exists() or not filecmp.cmp(source_path, target_path, shallow=False)
            ):
                stop_animation(animation_thread)
                print()  # Clear the animation line

                if sync_file(source_path, target_path):
                    changed_files.append(str(rel_path))

                animation_thread = start_animation(f"Syncing {source_dir.name}...", "blue")

    finally:
        stop_animation(animation_thread)

    return changed_files


@handle_keyboard_interrupt(message="Sync interrupted by user.", use_logging=True)
def sync_instances(source_root: Path, target_root: Path) -> None:
    """Sync specified directories and files between instances."""
    changes_made = []

    # Sync directories
    for dir_name in SYNC_DIRS:
        source_dir = source_root / dir_name
        target_dir = target_root / dir_name

        if not source_dir.exists():
            logger.warning("Source directory does not exist: %s", source_dir)
            continue

        changed = sync_directory(source_dir, target_dir)
        changes_made.extend(f"{dir_name}/{file}" for file in changed)

    # Sync individual files
    for file_path in SYNC_FILES:
        source_file = source_root / file_path
        target_file = target_root / file_path

        if sync_file(source_file, target_file):
            changes_made.append(file_path)

    if changes_made:
        logger.info("Synced files:\n  %s", "\n  ".join(changes_made))
    else:
        logger.info("No changes needed.")


@handle_keyboard_interrupt(message="Sync interrupted by user.", use_logging=True)
def main() -> None:
    """Sync files between prod and dev instances."""
    if confirm_action("Sync from prod to dev?", prompt_color="yellow"):
        sync_instances(PROD_ROOT, DEV_ROOT)
    elif confirm_action("Sync from dev to prod?", prompt_color="red"):
        sync_instances(DEV_ROOT, PROD_ROOT)


if __name__ == "__main__":
    main()
