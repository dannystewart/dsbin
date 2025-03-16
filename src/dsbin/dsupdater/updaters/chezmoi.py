from __future__ import annotations

import platform
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from dsbase.shell import handle_keyboard_interrupt

from dsbin.dsupdater.update_manager import UpdateManager, UpdateStage, UpdateStageFailedError

if TYPE_CHECKING:
    from logging import Logger


@dataclass
class ChezmoiPackageManager(UpdateManager):
    """Chezmoi package manager."""

    display_name: str = "chezmoi"
    description: str = "Chezmoi dotfile sync"
    prerequisite: str | None = "chezmoi"
    sort_order: int = 10

    logger: Logger = field(init=False)

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "update": UpdateStage(
            command="chezmoi update",
            start_message="Updating dotfiles...",
            error_message="Failed to update dotfiles: %s",
            filter_output=True,
            raise_error=True,
        ),
    }

    @handle_keyboard_interrupt()
    def perform_update_stages(self) -> None:
        """Update dotfiles using Chezmoi."""
        try:
            self.run_stage("update")
        except UpdateStageFailedError as e:
            if platform.system() == "Windows":
                # Errors are to be expected on Windows, so treat them as warnings
                self.updater.logger.warning(
                    "[%s] Chezmoi encountered an error and is not fully supported on Windows.",
                    self.display_name,
                )
                self.updater.logger.warning("[%s] %s", self.display_name, str(e))
            else:
                self.updater.logger.error("[%s] %s", self.display_name, str(e))
