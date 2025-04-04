from __future__ import annotations

import platform
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from polykit.shell import handle_interrupt

from dsbin.updater.update_manager import UpdateManager, UpdateStage, UpdateStageFailedError

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
        "status": UpdateStage(
            command="chezmoi status",
            capture_output=True,
            filter_output=True,
        ),
        "update": UpdateStage(
            command="chezmoi update",
            start_message="Updating dotfiles...",
            error_message="Failed to update dotfiles: %s",
            raise_error=True,
        ),
    }

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Update dotfiles using Chezmoi."""
        try:  # Check for changes first before attempting to update
            success, output = self.run_stage("status")
            if success and output and output.strip():
                self.logger.debug("[%s] Found changes to apply.", self.display_name)
                self.run_stage("update")
            else:
                self.logger.debug("[%s] Chezmoi is up to date.", self.display_name)

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
