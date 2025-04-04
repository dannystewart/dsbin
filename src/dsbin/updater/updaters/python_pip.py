from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import ClassVar

from polykit.shell import handle_interrupt

from dsbin.updater.update_manager import UpdateManager, UpdateStage


@dataclass
class PythonPipUpdater(UpdateManager):
    """Python package updater using pip."""

    display_name: str = "pip"
    description: str = "update local Python packages via pip"
    prerequisite: str | None = "pip"

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "upgrade-pip": UpdateStage(
            command="pip install --upgrade pip",
            start_message="Ensuring pip is up to date...",
            error_message="Failed to update pip: %s",
            filter_output=True,
        ),
        "list-packages": UpdateStage(
            command="pip freeze",
            capture_output=True,
            raise_error=True,
        ),
        "update": UpdateStage(
            command="",
            start_message="Updating locally installed Python packages...",
            end_message="Python packages updated successfully.",
            error_message="Failed to update Python packages: %s",
            filter_output=True,
        ),
    }

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Update pip itself, then update all installed packages."""
        # First upgrade pip itself
        self.run_stage("upgrade-pip")

        # Stop here on Windows
        if platform.system() == "Windows":
            self.logger.warning(
                "[%s] Python package updates are not supported on Windows.", self.display_name
            )
            return

        # Get list of installed packages
        success, output = self.run_stage("list-packages")
        if not success or not output:
            self.logger.error("[%s] Failed to get list of installed packages.", self.display_name)
            return

        # Process the package list
        packages = []
        for line in output.splitlines():
            # Skip packages installed from URLs or local files (contains @ symbol)
            if "@" in line:
                continue
            # Get package name before the version specifier
            package = line.split("==")[0]
            packages.append(package)

        if not packages:
            self.logger.info("[%s] No packages to update.", self.display_name)
            return

        # Update the command in the update stage with our package list
        update_stage = self.update_stages["update"]
        update_stage.command = f"pip install -U {' '.join(packages)}"

        # Run the update
        self.run_stage("update")
