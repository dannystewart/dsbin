from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from dsbin.dsupdater.update_manager import UpdateManager, UpdateStage

from dsutil.shell import handle_keyboard_interrupt


@dataclass
class ChezmoiPackageManager(UpdateManager):
    """Chezmoi package manager."""

    display_name: str = "chezmoi"
    description: str = "Chezmoi dotfile sync"
    prerequisite: str | None = "chezmoi"
    sort_order = 10

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "update": UpdateStage(
            command="chezmoi update",
            start_message="Updating dotfiles...",
            error_message="Failed to update dotfiles: %s",
            filter_output=True,
        ),
    }

    @handle_keyboard_interrupt()
    def perform_update_stages(self) -> None:
        """Update dotfiles using Chezmoi."""
        self.run_stage("update")
