from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from polykit.shell import handle_interrupt

from dsbin.updater.update_manager import UpdateManager, UpdateStage


@dataclass
class DSPackageUpdater(UpdateManager):
    """Updater for DS Python packages."""

    display_name: str = "ds"
    description: str = "install or update dsbin and related packages"
    prerequisite: str | None = "dsbin"
    sort_order: int = 5

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "install": UpdateStage(
            command="pip install --upgrade dsbin",
            start_message="Installing dsbin...",
            end_message="dsbin installed successfully!",
            capture_output=True,
            filter_output=True,
        ),
    }

    def __post_init__(self):
        super().__post_init__()

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Update pip itself, then update all installed packages."""
        self.run_stage("install")
