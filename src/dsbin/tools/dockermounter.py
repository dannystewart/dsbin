#!/usr/bin/env python3

"""Checks to see if mount points are mounted, and act accordingly."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from dsutil.log import LocalLogger
from dsutil.paths import DSPaths

paths = DSPaths("dockermounter")
LOG_FILE_PATH = paths.get_log_path("dockermounter.log")

logger = LocalLogger.setup_logger(log_file=LOG_FILE_PATH)

POSSIBLE_SHARES = ["Danny", "Downloads", "Music", "Media", "Storage"]


@dataclass
class ShareManager:
    """
    Manage shared directories, checking their mount status and handling Docker stacks.

    Checks mount status and directory contents, remounts all filesystems, and restarts Docker stacks
    if necessary. Designed to work with command-line arguments and can be run automatically.

    Attributes:
        mount_root: The root directory where shares are mounted.
        docker_compose: Path to docker-compose file to control Docker stack.
        auto: Whether to automatically fix share issues without user confirmation.
    """

    mount_root: Path
    docker_compose: Path | None
    auto: bool

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> ShareManager:
        """Create a ShareManager instance from command-line arguments."""
        return cls(
            mount_root=Path("/mnt"),
            docker_compose=Path(args.docker).expanduser() if args.docker else None,
            auto=args.auto,
        )

    def get_active_shares(self) -> list[Path]:
        """Get list of share directories that actually exist."""
        return [
            self.mount_root / share
            for share in POSSIBLE_SHARES
            if (self.mount_root / share).exists()
        ]

    def is_mounted(self, path: Path) -> bool:
        """Check if a path is currently mounted."""
        try:
            path_stat = path.stat()
            parent_stat = path.parent.stat()
            return path_stat.st_dev != parent_stat.st_dev
        except Exception as e:
            logger.error("Failed to check mount status for %s: %s", path, e)
            return False

    def has_contents(self, path: Path) -> bool:
        """Check if a directory has any contents."""
        return any(path.iterdir())

    def clean_directory(self, path: Path) -> bool:
        """Remove all contents from a directory while preserving the directory itself."""
        try:
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info("Cleaned directory %s", path)
            return True
        except Exception as e:
            logger.error("Failed to clean directory %s: %s", path, e)
            return False

    def remount_all(self) -> bool:
        """Remount all filesystems."""
        try:
            subprocess.run(["sudo", "mount", "-a"], check=True)
            logger.info("Successfully remounted all filesystems")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to remount filesystems: %s", e)
            return False

    def restart_docker(self) -> bool:
        """Restart the Docker stack if docker-compose path was provided."""
        if not self.docker_compose:
            return True

        try:
            compose_dir = self.docker_compose.parent
            subprocess.run(["docker-compose", "down"], check=True, cwd=compose_dir)
            logger.info("Docker stack is down")

            subprocess.run(["docker-compose", "up", "-d"], check=True, cwd=compose_dir)
            logger.info("Docker stack is up")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restart Docker stack: %s", e)
            return False

    def check_shares(self) -> tuple[list[Path], list[Path]]:
        """Check all shares and return a tuple of (unmounted shares with contents, all unmounted shares)."""
        unmounted_with_content = []
        unmounted = []

        for share in self.get_active_shares():
            if not self.is_mounted(share):
                unmounted.append(share)
                if self.has_contents(share):
                    unmounted_with_content.append(share)
                    logger.warning("%s: Share is not mounted but has contents.", share)
                else:
                    logger.info("%s: Share is not mounted.", share)
            else:
                logger.info("%s: Share is properly mounted.", share)

        return unmounted_with_content, unmounted

    def fix_shares(self) -> bool:
        """Fix any share mounting issues."""
        problematic, unmounted = self.check_shares()

        if not unmounted:
            logger.info("All shares are properly mounted.")
            return True
        if problematic:
            if not self.auto:
                shares_str = "\n  ".join(str(p) for p in problematic)
                response = input(
                    f"The following shares have contents but aren't mounted:\n"
                    f"  {shares_str}\n"
                    f"Do you want to clean them? (y/N): "
                ).lower()

                if response != "y":
                    logger.info("User chose not to clean shares")
                    return False

            # Clean problematic shares
            for share in problematic:
                if not self.clean_directory(share):
                    return False

        # Remount everything
        if not self.remount_all():
            return False

        # Restart Docker if configured
        return self.restart_docker()


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for managing network shares and Docker services."""
    parser = argparse.ArgumentParser(description="Manage network shares and Docker services")
    parser.add_argument(
        "--check", action="store_true", help="Only check share status without making changes"
    )
    parser.add_argument(
        "--docker",
        help="Path to docker-compose.yml for restarting services",
        default="~/docker/docker-compose.yml",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Don't prompt for confirmation before cleaning shares",
    )
    return parser.parse_args()


def main() -> int:
    """Main function for handling share management operations."""
    args = parse_args()
    manager = ShareManager.from_args(args)

    if args.check:
        problematic, unmounted = manager.check_shares()
        return 1 if unmounted else 0

    if manager.fix_shares():
        logger.info("All operations completed successfully.")
        return 0
    logger.error("Failed to fix share issues.")
    return 1


if __name__ == "__main__":
    exit(main())
