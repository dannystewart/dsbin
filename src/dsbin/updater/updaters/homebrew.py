from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from polykit.cli import handle_interrupt

from dsbin.updater.update_manager import UpdateManager, UpdateStage


@dataclass
class HomebrewPackageManager(UpdateManager):
    """Homebrew package manager."""

    display_name: str = "homebrew"
    description: str = "Homebrew package manager"
    prerequisite: str | None = "brew"

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "update": UpdateStage(
            command="brew update",
            start_message="Updating package list...",
        ),
        "upgrade": UpdateStage(
            command="brew upgrade",
            start_message="Upgrading packages...",
        ),
        "cleanup": UpdateStage(
            command="brew cleanup",
            start_message="Cleaning up old packages...",
        ),
    }

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Update packages using Homebrew."""
        self.run_stage("update")
        self.run_stage("upgrade")
        self.run_stage("cleanup")
