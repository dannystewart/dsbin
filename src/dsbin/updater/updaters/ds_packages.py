from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from dsbase.util import handle_interrupt
from dsbase.version import VersionChecker

from dsbin.updater.update_manager import UpdateManager, UpdateStage


@dataclass
class DSPackageUpdater(UpdateManager):
    """Updater for DS Python packages."""

    display_name: str = "ds"
    description: str = "install or update dsbin and related packages"
    prerequisite: str | None = "dsbin"
    sort_order: int = 5

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "uninstall": UpdateStage(
            command="pip uninstall -y dsbin dsbase",
            start_message="Uninstalling dsbin and dsbase for clean install...",
            capture_output=True,
            filter_output=True,
        ),
        "install": UpdateStage(
            command="pip install --upgrade git+ssh://git@github.com/dannystewart/dsbin.git",
            start_message="Installing dsbin...",
            end_message="dsbin installed successfully!",
            capture_output=True,
            filter_output=True,
        ),
    }

    def __post_init__(self):
        super().__post_init__()
        self.version_checker = VersionChecker()

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Update pip itself, then update all installed packages."""
        # Get current package versions before uninstalling
        dsbin_old = self.version_checker.get_installed_version("dsbin")
        dsbase_old = self.version_checker.get_installed_version("dsbase")

        # Uninstall the existing packages to ensure a clean install
        self.run_stage("uninstall")

        # Get latest package version numbers
        dsbin_new = self.version_checker.get_pypi_version("dsbin")
        dsbase_new = self.version_checker.get_pypi_version("dsbase")

        # Formulate the end message with the version information
        if dsbin_old and dsbin_new and dsbin_old != dsbin_new:
            dsbin_str = f"dsbin {dsbin_old} -> {dsbin_new}"
        else:
            dsbin_str = f"dsbin {dsbin_new}" if dsbin_new else "dsbin"

        if dsbase_old and dsbase_new and dsbase_old != dsbase_new:
            dsbase_str = f" and dsbase {dsbase_old} -> {dsbase_new}"
        else:
            dsbase_str = f" and dsbase {dsbase_new}" if dsbase_new else ""

        end_message = f"Installed {dsbin_str}{dsbase_str} successfully!"

        self.update_stages["install"].end_message = end_message
        self.run_stage("install")
