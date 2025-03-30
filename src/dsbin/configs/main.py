"""Download configs for coding tools and compare against local versions.

This script is designed to download configuration files for various coding tools (e.g., ruff, mypy)
to compare against files with the same name in the directory where the script is run. This is to
ensure that I always have the latest versions of my preferred configurations for all my projects.

Note that these config files live in the dsbase repository: https://github.com/dannystewart/dsbase

The script also saves the updated config files to the package root, which is the root of the dsbase
repository itself, thereby creating a virtuous cycle where the repo is always up-to-date with the
latest versions of the config files for other projects to pull from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import requests

from dsbase import ArgParser, FileManager, LocalLogger
from dsbase.shell import confirm_action
from dsbase.text.diff import show_diff

if TYPE_CHECKING:
    import argparse


@dataclass
class ConfigFile:
    """Represents a config file that can be updated from a remote source."""

    # Base URL for the repository
    CONFIG_ROOT: ClassVar[str] = (
        "https://raw.githubusercontent.com/dannystewart/dsbase/refs/heads/main"
    )

    name: str
    url: str = field(init=False)
    local_path: Path = field(init=False)

    def __post_init__(self):
        self.url = f"{self.CONFIG_ROOT}/{self.name}"
        self.local_path = Path.cwd() / self.name


class ConfigManager:
    """Manages downloading and updating config files from a remote repository."""

    # Define the configs to manage
    CONFIGS: ClassVar[list[ConfigFile]] = [
        ConfigFile("ruff.toml"),
        ConfigFile("mypy.ini"),
    ]

    def __init__(self, skip_confirm: bool = False):
        self.logger = LocalLogger().get_logger()
        self.files = FileManager()
        self.skip_confirm = skip_confirm
        self.changes_made = set()

        if self._should_create_all:
            self.logger.debug(
                "No existing configs found; downloading and creating all available configs."
            )

    def update_configs(self) -> None:
        """Pull down latest configs from repository, updating local copies."""
        for config in self.CONFIGS:
            remote_content = self.fetch_remote_content(config)
            if not remote_content:
                self.logger.error(
                    "Failed to update %s config - not available remotely.", config.name
                )
                continue

            if self.process_config(config, remote_content):
                self.changes_made.add(config.name)

        # Report unchanged configs
        if unchanged := [c.name for c in self.CONFIGS if c.name not in self.changes_made]:
            self.logger.info("No changes needed for: %s", ", ".join(unchanged))

    def fetch_remote_content(self, config: ConfigFile) -> str | None:
        """Fetch content from remote URL."""
        try:
            response = requests.get(config.url)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            self.logger.warning("Failed to download %s from remote.", config.name)
            return None

    def process_config(self, config: ConfigFile, remote_content: str) -> bool:
        """Process a single config file, updating or creating as needed.

        Returns:
            True if the config was updated or created, False otherwise.
        """
        if config.local_path.exists():
            local_content = config.local_path.read_text()
            if local_content == remote_content:
                return False

            if not self.skip_confirm:
                show_diff(local_content, remote_content, config.local_path.name)
                if not confirm_action(f"Update {config.name} config?", default_to_yes=True):
                    return False
        elif not (
            self.skip_confirm
            or self._should_create_all
            or confirm_action(
                f"{config.name} config does not exist locally. Create?",
                default_to_yes=True,
            )
        ):
            return False

        # Write the file and log it
        config.local_path.write_text(remote_content)
        self.logger.info(
            "%s %s config from remote.",
            "Created" if not config.local_path.exists() else "Updated",
            config.name,
        )
        return True

    @property
    def _should_create_all(self) -> bool:
        return not any(config.local_path.exists() for config in self.CONFIGS)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = ArgParser(description="Update config files from central repository")
    parser.add_argument("-y", action="store_true", help="update files without confirmation")
    return parser.parse_args()


def main() -> None:
    """Fetch and update the config files."""
    args = parse_args()
    manager = ConfigManager(skip_confirm=args.y)
    manager.update_configs()


if __name__ == "__main__":
    main()
