from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from dsutil.shell import handle_keyboard_interrupt

from dsbin.dsupdater.update_manager import UpdateManager, UpdateStage


@dataclass
class DSPackageUpdater(UpdateManager):
    """Updater for DS Python packages."""

    display_name: str = "dsbin"
    description: str = "install or update dsbin and related packages"
    prerequisite: str | None = "pip"
    sort_order: int = 5

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "uninstall": UpdateStage(
            command="pip uninstall -y dsbin dsutil",
            start_message="Uninstalling dsbin and dsutil for clean install...",
            capture_output=True,
            filter_output=True,
        ),
        "install": UpdateStage(
            command="pip install --upgrade git+https://gitlab.dannystewart.com/danny/dsbin.git",
            start_message="Installing dsbin...",
            end_message="dsbin installed successfully!",
            capture_output=True,
            filter_output=True,
        ),
    }

    @handle_keyboard_interrupt()
    def perform_update_stages(self) -> None:
        """Update pip itself, then update all installed packages."""
        self.run_stage("uninstall")
        self.run_stage("install")
