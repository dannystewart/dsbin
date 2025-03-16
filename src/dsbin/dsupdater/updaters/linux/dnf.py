from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from dsbase.shell import handle_keyboard_interrupt

from dsbin.dsupdater.update_manager import UpdateManager, UpdateStage


@dataclass
class DNFPackageManager(UpdateManager):
    """DNF package manager for Fedora-based systems."""

    display_name: str = "dnf"
    description: str = "DNF package manager for Fedora-based systems"
    prerequisite: str | None = "dnf"
    requires_sudo: bool = True

    system_updater: ClassVar[bool] = True
    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "upgrade": UpdateStage(
            command="dnf upgrade -y",
            start_message="Updating packages...",
            requires_sudo=True,
        ),
    }

    @handle_keyboard_interrupt()
    def perform_update_stages(self) -> None:
        """Update packages using DNF."""
        self.run_stage("upgrade")
