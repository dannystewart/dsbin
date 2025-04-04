from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from polykit.shell import handle_interrupt

from dsbin.updater.update_manager import UpdateManager, UpdateStage


@dataclass
class MacOSSoftwareUpdate(UpdateManager):
    """SoftwareUpdate for macOS."""

    display_name: str = "macOS"
    description: str = "macOS software update command"
    prerequisite: str | None = "softwareupdate"
    skip_auto_add: bool = True

    system_updater: ClassVar[bool] = True
    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "force_install_now": UpdateStage(
            command="softwareupdate -ia --force",
            start_message="Installing all available updates...",
        ),
        "check_in_background": UpdateStage(
            command="softwareupdate --background",
            start_message="Starting background update check...",
            end_message="Updates will appear in System Settings > Software Update if available.",
            requires_sudo=True,
        ),
    }

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Install updates using softwareupdate."""
        self.run_stage("check_in_background")

    @handle_interrupt()
    def force_install_now(self) -> None:
        """Check for updates in the background."""
        self.run_stage("force_install_now")
