#!/usr/bin/env python3

"""Checks to see if mount points are mounted, and act accordingly.

To have this run automatically, create the service and timer:

# /etc/systemd/system/dockermounter.service
[Unit]
Description=Check and fix Docker mount points
After=network.target

[Service]
Type=oneshot
ExecStart=/home/USER/.pyenv/shims/dockermounter --auto
User=root
Environment=PYENV_ROOT=/home/YOUR_USERNAME/.pyenv
Environment=PATH=/home/YOUR_USERNAME/.pyenv/shims:/home/YOUR_USERNAME/.pyenv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/dockermounter.timer
[Unit]
Description=Run Docker mount checker periodically

[Timer]
# Run every 15 minutes
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target

Then install the service and timer:

> sudo cp dockermounter.py /home/USER/.pyenv/shims/dockermounter
> sudo chmod +x /home/USER/.pyenv/shims/dockermounter
> sudo systemctl daemon-reload
> sudo systemctl enable dockermounter.timer
> sudo systemctl start dockermounter.timer

"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from enviromancer import Enviromancer
from logician import Logician
from pathkeeper import PathKeeper
from polykit.cli import confirm_action
from polykit.shell import is_root_user

from dsbin.util.notify import TelegramSender

if TYPE_CHECKING:
    from logging import Logger

paths = PathKeeper("dockermounter")
LOG_FILE_PATH = paths.from_log("dockermounter.log")
logger = Logician.get_logger(log_file=LOG_FILE_PATH)

POSSIBLE_SHARES = ["USER", "Downloads", "Music", "Media", "Storage"]


def setup_env() -> Enviromancer:
    """Setup environment configuration."""
    env = Enviromancer()
    env.add_var(
        "TELEGRAM_BOT_TOKEN",
        description="Telegram Bot API token for notifications",
        secret=True,
        required=False,
    )
    env.add_var(
        "TELEGRAM_CHAT_ID",
        description="Telegram chat ID for notifications",
        required=False,
    )
    env.add_var(
        "NOTIFY_ON_CHECK",
        description="Send notification even when all mounts are okay",
        required=False,
        default="false",
        var_type=lambda x: x.lower() == "true",
    )
    return env


@dataclass
class ShareManager:
    """Manage shared directories, checking their mount status and handling Docker stacks.

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

    env: Enviromancer = field(init=False)
    telegram: TelegramSender | None = field(init=False)
    logger: Logger = field(init=False)

    def __post_init__(self):
        """Initialize environment and optional Telegram notification.

        Raises:
            ValueError: If mount_root or docker_compose does not exist.
        """
        # Validate mount_root
        if not self.mount_root.is_dir():
            msg = f"Mount root directory does not exist: {self.mount_root}"
            raise ValueError(msg)

        # Validate docker_compose if provided
        if self.docker_compose and not self.docker_compose.is_file():
            msg = f"Docker compose file does not exist: {self.docker_compose}"
            raise ValueError(msg)

        # Setup environment and notifications
        self.env = setup_env()
        self.logger = Logician.get_logger()

        self.telegram = None
        if self.env.telegram_bot_token and self.env.telegram_chat_id:
            self.telegram = TelegramSender(self.env.telegram_bot_token, self.env.telegram_chat_id)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> ShareManager:
        """Create a ShareManager instance from command-line arguments."""
        docker_path = None
        if args.docker:
            path = Path(args.docker).expanduser()
            if path.exists():
                docker_path = path
            else:
                logger.warning(
                    "Docker Compose file %s not found, skipping Docker operations.", path
                )

        return cls(
            mount_root=Path("/mnt"),
            docker_compose=docker_path,
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
            subprocess.run(["sudo", "mount", "-a"], check=True, timeout=30)
            logger.info("Successfully remounted all filesystems.")
            return True
        except subprocess.TimeoutExpired:
            logger.error("Timeout while trying to remount filesystems.")
            return False
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
            logger.info("Docker stack is down.")

            subprocess.run(["docker-compose", "up", "-d"], check=True, cwd=compose_dir)
            logger.info("Docker stack is up.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to restart Docker stack: %s", e)
            return False

    def check_shares(self) -> tuple[list[Path], list[Path]]:
        """Check shares and return tuple of (unmounted with contents, all unmounted)."""
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
                if not confirm_action(
                    f"The following shares have contents but aren't mounted:\n"
                    f"  {shares_str}\nDo you want to clean them? (y/N): "
                ):
                    logger.info("Not cleaning shares.")
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
        "--docker", help="Path to docker-compose.yml, to restart services if desired.", default=""
    )
    parser.add_argument(
        "--auto", action="store_true", help="Don't prompt for confirmation before cleaning shares"
    )
    return parser.parse_args()


def main() -> int:
    """Main function for handling share management operations."""
    if not is_root_user():
        logger.error("This script must be run as root.")
        return 1

    args = parse_args()
    manager = ShareManager.from_args(args)

    if args.check:
        _, unmounted = manager.check_shares()
        return 1 if unmounted else 0

    if manager.fix_shares():
        logger.info("All operations completed successfully.")
        return 0
    logger.error("Failed to fix share issues.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
