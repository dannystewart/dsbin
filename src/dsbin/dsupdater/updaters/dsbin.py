from __future__ import annotations

import importlib.metadata
import subprocess
from dataclasses import dataclass
from typing import ClassVar

from packaging import version

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

    def _get_installed_version(self, package: str) -> str | None:
        """Get the currently installed version of a package."""
        try:
            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None

    def _get_latest_version(self, package: str) -> str | None:
        """Get latest version from GitLab."""
        gitlab_base = "https://gitlab.dannystewart.com/danny"
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--tags", f"{gitlab_base}/{package}.git"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Get all version tags and clean them up
            versions = []
            for ref in result.stdout.splitlines():
                tag = ref.split("/")[-1]
                if tag.startswith("v"):
                    # Clean up Git ref notation and parse version
                    clean_tag = tag.split("^")[0]
                    try:
                        versions.append(version.parse(clean_tag))
                    except version.InvalidVersion:
                        continue

            # Sort with packaging.version comparison
            if versions:
                return str(max(versions))
            return None

        except subprocess.CalledProcessError:
            return None

    @handle_keyboard_interrupt()
    def perform_update_stages(self) -> None:
        """Update pip itself, then update all installed packages."""
        # Get current package versions before uninstalling
        dsbin_old = self._get_installed_version("dsbin")
        dsutil_old = self._get_installed_version("dsutil")

        # Uninstall the existing packages to ensure a clean install
        self.run_stage("uninstall")

        # Get latest package version numbers
        dsbin_new = self._get_latest_version("dsbin")
        dsutil_new = self._get_latest_version("dsutil")

        # Formulate the end message with the version information
        if dsbin_old and dsbin_new and dsbin_old != dsbin_new:
            dsbin_str = f"dsbin {dsbin_old} -> {dsbin_new}"
        else:
            dsbin_str = f"dsbin {dsbin_new}" if dsbin_new else "dsbin"

        if dsutil_old and dsutil_new and dsutil_old != dsutil_new:
            dsutil_str = f" and dsutil {dsutil_old} -> {dsutil_new}"
        else:
            dsutil_str = f" and dsutil {dsutil_new}" if dsutil_new else ""

        end_message = f"{dsbin_str}{dsutil_str} installed successfully!"

        self.update_stages["install"].end_message = end_message
        self.run_stage("install")
