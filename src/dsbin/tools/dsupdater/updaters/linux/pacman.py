from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from dsbin.tools.dsupdater.update_manager import UpdateManager, UpdateStage

from dsutil.shell import handle_keyboard_interrupt


@dataclass
class PacmanPackageManager(UpdateManager):
    """Pacman package manager for Arch-based systems."""

    display_name: str = "pacman"
    description: str = "Pacman package manager for Arch-based systems"
    prerequisite: str | None = "pacman"
    requires_sudo: bool = True

    system_updater = True
    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "upgrade": UpdateStage(
            command="pacman -Syu --noconfirm",
            start_message="Updating packages...",
            requires_sudo=True,
        ),
    }

    @handle_keyboard_interrupt()
    def perform_update_stages(self) -> None:
        """Update packages using Pacman."""
        self.run_stage("upgrade")
