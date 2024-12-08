from __future__ import annotations

import filecmp
import platform
import shutil
import socket
from typing import TYPE_CHECKING

from dsutil import LocalLogger
from dsutil.animation import start_animation, stop_animation
from dsutil.diff import DiffResult, show_diff
from dsutil.shell import confirm_action, handle_keyboard_interrupt

if TYPE_CHECKING:
    from pathlib import Path

    from .config import BotControlConfig


class InstanceSync:
    """Handles synchronization between prod and dev instances."""

    def __init__(self, config: BotControlConfig):
        self.config = config
        self.logger = LocalLogger.setup_logger()
        self._validate_environment()

    def _validate_environment(self) -> None:
        """Validate the execution environment."""
        # Check if running on allowed host
        hostname = socket.gethostname().lower()
        fqdn = socket.getfqdn().lower()

        allowed_hosts = [host.lower() for host in self.config.allowed_hosts]
        if not any(
            hostname == host or fqdn == host or hostname.startswith(host) for host in allowed_hosts
        ):
            msg = (
                f"This script can only run on allowed hosts: {', '.join(self.config.allowed_hosts)}\n"
                f"Current hostname: {hostname} ({fqdn})"
            )
            raise RuntimeError(msg)

        # Check if running on Linux
        if platform.system() != "Linux":
            msg = "This script is designed to run on Linux systems only"
            raise RuntimeError(msg)

        # Validate paths exist
        if not self.config.prod_root.exists():
            msg = f"Production root does not exist: {self.config.prod_root}"
            raise RuntimeError(msg)
        if not self.config.dev_root.exists():
            msg = f"Development root does not exist: {self.config.dev_root}"
            raise RuntimeError(msg)

    def _should_exclude(self, path: Path) -> bool:
        """Check if a file should be excluded based on patterns."""
        return any(
            path.match(pattern) or pattern in str(path) for pattern in self.config.exclude_patterns
        )

    @handle_keyboard_interrupt(message="Sync interrupted by user.", use_logging=True)
    def sync_file(self, source: Path, target: Path) -> bool:
        """Sync a single file, showing diff if text file."""
        if not source.exists():
            self.logger.warning("Source file does not exist: %s", source)
            return False

        # New file
        if not target.exists():
            return self._handle_new_file(source, target)

        # Existing file
        if filecmp.cmp(source, target, shallow=False):
            return False

        return self._handle_existing_file(source, target)

    def _handle_new_file(self, source: Path, target: Path) -> bool:
        """Handle synchronization of a new file."""
        self.logger.warning("New file: %s", source.name)
        self.logger.info("  Source: %s", source)
        self.logger.info("  Size: %s bytes", source.stat().st_size)

        if confirm_action("Create new file?", prompt_color="yellow"):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return True
        return False

    def _handle_existing_file(self, source: Path, target: Path) -> bool:
        """Handle synchronization of an existing file."""
        try:
            current = target.read_text()
            new = source.read_text()
            result = show_diff(current, new, target.name)
            self._show_diff_summary(current, new, target.name, result)
        except UnicodeDecodeError:
            self._show_binary_file_info(source, target)

        if confirm_action(f"Update {target.name}?", prompt_color="yellow"):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            return True

        return False

    def _show_diff_summary(self, current: str, new: str, filename: str, result: DiffResult) -> None:
        """Show summary of file differences."""
        if not current:
            self.logger.warning("File will be created: %s", filename)
            self.logger.info("  Lines: %d", len(new.splitlines()))
        elif not new:
            self.logger.warning("File will be deleted: %s", filename)
            self.logger.info("  Current lines: %d", len(current.splitlines()))
        else:
            self.logger.info("Changes: +%d -%d lines", len(result.additions), len(result.deletions))

    def _show_binary_file_info(self, source: Path, target: Path) -> None:
        """Show information about binary file changes."""
        self.logger.warning("Binary file detected: %s", target.name)
        self.logger.info("  Source: %s", source)
        self.logger.info("  Target: %s", target)
        self.logger.info("  Size: %s -> %s bytes", target.stat().st_size, source.stat().st_size)

    @handle_keyboard_interrupt(message="Sync interrupted by user.", use_logging=True)
    def sync_directory(self, source_dir: Path, target_dir: Path) -> list[str]:
        """Sync a directory, returning list of changed files."""
        changed_files = []
        target_dir.mkdir(parents=True, exist_ok=True)

        animation_thread = start_animation(f"Syncing {source_dir.name}...", "blue")

        try:
            for source_path in source_dir.rglob("*"):
                if self._should_exclude(source_path):
                    continue

                rel_path = source_path.relative_to(source_dir)
                target_path = target_dir / rel_path

                if source_path.is_file() and (
                    not target_path.exists()
                    or not filecmp.cmp(source_path, target_path, shallow=False)
                ):
                    stop_animation(animation_thread)
                    print()  # Clear animation line

                    if self.sync_file(source_path, target_path):
                        changed_files.append(str(rel_path))

                    animation_thread = start_animation(f"Syncing {source_dir.name}...", "blue")

        finally:
            stop_animation(animation_thread)

        return changed_files

    @handle_keyboard_interrupt(message="Sync interrupted by user.", use_logging=True)
    def sync_instances(self, source_root: Path, target_root: Path) -> None:
        """Sync specified directories and files between instances."""
        changes_made = []

        # Sync directories
        for dir_name in self.config.sync_dirs:
            source_dir = source_root / dir_name
            target_dir = target_root / dir_name

            if not source_dir.exists():
                self.logger.warning("Source directory does not exist: %s", source_dir)
                continue

            changed = self.sync_directory(source_dir, target_dir)
            changes_made.extend(f"{dir_name}/{file}" for file in changed)

        # Sync individual files
        for file_path in self.config.sync_files:
            source_file = source_root / file_path
            target_file = target_root / file_path

            if self.sync_file(source_file, target_file):
                changes_made.append(file_path)
        if changes_made:
            self.logger.info("Synced files:\n  %s", "\n  ".join(changes_made))
        else:
            self.logger.info("No changes needed.")

    def sync(self, prod_to_dev: bool | None = None) -> None:
        """Sync files between prod and dev instances."""
        if prod_to_dev is None:
            if confirm_action("Sync from prod to dev?", prompt_color="yellow"):
                prod_to_dev = True
            elif confirm_action("Sync from dev to prod?", prompt_color="red"):
                prod_to_dev = False
            else:
                return

        source = self.config.prod_root if prod_to_dev else self.config.dev_root
        target = self.config.dev_root if prod_to_dev else self.config.prod_root
        self.sync_instances(source, target)
