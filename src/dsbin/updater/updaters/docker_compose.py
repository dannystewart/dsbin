from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from polykit.cli import handle_interrupt

from dsbin.updater.update_manager import UpdateManager, UpdateStage, UpdateStageFailedError


@dataclass
class DockerComposeUpdater(UpdateManager):
    """Docker Compose updater."""

    display_name: str = "docker"
    description: str = "pull Docker images, if docker-compose.yml is in this directory"
    prerequisite: str | None = "docker"

    update_stages: ClassVar[dict[str, UpdateStage]] = {
        "pull": UpdateStage(
            command="docker compose pull",
            start_message="Pulling latest Docker images...",
            end_message="Docker images updated successfully.",
            error_message="Failed to pull Docker images: %s",
            capture_output=True,
            raise_error=True,
        ),
    }

    @handle_interrupt()
    def perform_update_stages(self) -> None:
        """Update Docker images if docker-compose.yml is present."""
        if not Path("docker-compose.yml").is_file():
            self.logger.debug(
                "[%s] No docker-compose.yml found in current directory. Skipping.",
                self.display_name,
            )
            return
        self.logger.debug("[%s] Found docker-compose.yml in current directory.", self.display_name)

        try:
            self.run_stage("pull")
        except UpdateStageFailedError as e:
            if "must be built from source" in str(e):
                self.logger.warning(
                    "[%s] Docker images updated, but some must be built manually.",
                    self.display_name,
                )
            elif "Pulled" in str(e) and "Warning" not in str(e):
                self.logger.info("[%s] Docker images updated successfully.", self.display_name)
            else:
                self.logger.warning(
                    "[%s] Some Docker images may not have updated successfully.", self.display_name
                )

            if self.debug:
                self.logger.debug("[%s] Full output:\n%s", self.display_name, str(e))
            return

        self.logger.info("[%s] Docker images updated successfully.", self.display_name)
