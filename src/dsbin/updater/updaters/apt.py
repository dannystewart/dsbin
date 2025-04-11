from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from polykit.cli import handle_interrupt

from dsbin.updater.update_manager import UpdateManager, UpdateStage


@dataclass
class APTPackageManager(UpdateManager):
    """APT package manager for Debian-based systems."""

    display_name: str = "apt"
    description: str = "APT package manager for Debian-based systems"
    prerequisite: str | None = "apt"
    requires_sudo: bool = True

    system_updater: ClassVar[bool] = True
    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "update": UpdateStage(
            command="apt update",
            start_message="Updating package list...",
            requires_sudo=True,
        ),
        "upgrade": UpdateStage(
            command="apt upgrade -y",
            start_message="Updating packages...",
            requires_sudo=True,
        ),
        "autoremove": UpdateStage(
            command="apt autoremove -y",
            start_message="Removing unneeded packages...",
            requires_sudo=True,
        ),
    }

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Update packages using APT."""
        self.run_stage("update")
        self.run_stage("upgrade")
        self.run_stage("autoremove")
