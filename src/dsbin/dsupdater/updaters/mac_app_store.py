from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from dsbase.shell import handle_keyboard_interrupt

from dsbin.dsupdater.update_manager import UpdateManager, UpdateStage


@dataclass
class MacAppStoreUpdate(UpdateManager):
    """Mac App Store updates."""

    display_name: str = "mas"
    description: str = "Mac App Store updates"
    prerequisite: str | None = "mas"

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "upgrade": UpdateStage(
            command="mas upgrade",
            start_message="Updating Mac App Store apps...",
        ),
    }

    @handle_keyboard_interrupt()
    def perform_update_stages(self) -> None:
        """Install updates using mas command."""
        self.run_stage("upgrade")
