"""This script will download config files for various coding tools which are then used as reference
to compare against files with the same name in the directory where the script is run. This is to
ensure that I always have the latest versions of my preferred configurations for all my projects.

Note that these config files live in the dsbin repository: https://github.com/dannystewart/dsbin

The script also saves the updated config files to the package root, which is the root of the dsbin
repository itself, thereby creating a virtuous cycle where the repo is always up-to-date with the
latest versions of the config files for other projects to pull from.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

import requests

from dsbase import EnvManager, FileManager, LocalLogger
from dsbase.shell import confirm_action
from dsbase.text.diff import show_diff
from dsbase.version import PackageSource, VersionChecker


@dataclass
class ConfigFile:
    """Represents a config file that can be updated from a remote source."""

    CONFIG_ROOT: ClassVar[str] = (
        "https://raw.githubusercontent.com/dannystewart/configs/refs/heads/main"
    )

    name: str
    url: str = field(init=False)
    path: Path = field(init=False)

    def __post_init__(self):
        self.url = f"{self.CONFIG_ROOT}/{self.name}"
        self.path = Path.cwd() / self.name


class CodeConfigs:
    """Class to manage all code-related config files."""

    # Config files to manage
    CONFIGS: ClassVar[list[ConfigFile]] = [
        ConfigFile("ruff.toml"),
        ConfigFile("mypy.ini"),
    ]

    # Package name for version checking
    PACKAGE_NAME: ClassVar[str] = "configs"

    # Comment format for version tracking in config files
    VERSION_COMMENT_FORMAT: ClassVar[dict[str, tuple[str, str]]] = {
        ".ini": ("; ", ""),
        ".json": ("// ", ""),
        ".py": ("# ", ""),
        ".toml": ("# ", ""),
        ".yaml": ("# ", ""),
        ".yml": ("# ", ""),
    }

    # Source for version checking
    VERSION_SOURCE: ClassVar[PackageSource] = PackageSource.AUTO

    def __init__(self, skip_confirm: bool = False):
        # Use EnvManager to get debug level for logging
        env = EnvManager()
        env.add_debug_var()

        self.logger = LocalLogger().get_logger(level=env.log_level)
        self.files = FileManager()
        self.version_checker = VersionChecker()

        # Get version info
        self.version_info = self.version_checker.check_package(
            self.PACKAGE_NAME, source=self.VERSION_SOURCE
        )

        # Debug path information
        self.logger.debug("Current working directory: %s", Path.cwd())
        for config in self.CONFIGS:
            self.logger.debug("Config %s path: %s", config.name, config.path)

        # Check if this is a first-time setup and skip confirmation if so, or if -y was used
        self.auto_confirm: bool = skip_confirm or self.first_time_setup
        if self.first_time_setup:
            self.logger.info("No configs found. Downloading all available configs.")

        # Log version information
        if self.version_info.current:
            self.logger.info("Latest config version: %s", self.get_latest_version())
        else:
            self.logger.warning("Package not installed. Using development version.")

        self.update_and_log()

    def update_and_log(self) -> None:
        """Update config files from remote source. Skip confirmation if auto_confirm is True."""
        was_first_time_setup = self.first_time_setup
        updated_configs, failed_configs, unchanged_configs = self.update_configs()

        if updated_configs and not was_first_time_setup:
            self.logger.info("Updated configs: %s", ", ".join(updated_configs))
        if unchanged_configs:
            self.logger.info("Already up-to-date: %s", ", ".join(unchanged_configs))
        if failed_configs:
            self.logger.warning("Failed to update: %s", ", ".join(failed_configs))

        if not updated_configs and not unchanged_configs and not failed_configs:
            self.logger.info("No configs processed.")
        elif not updated_configs:
            if failed_configs and not unchanged_configs:
                self.logger.info("No configs updated due to errors.")

    def update_configs(self) -> tuple[list[str], list[str], list[str]]:
        """Update config files from remote source."""
        updated_configs = []
        failed_configs = []
        unchanged_configs = []

        for config in self.CONFIGS:
            # Fetch content from remote source
            if content := self.fetch_remote_content(config):
                # Add version information to the content
                versioned_content = self.add_version_to_content(content, config.name)

                if config.path.exists():
                    # Check if config file needs updating
                    if self.needs_update(config.path):
                        result = self.update_existing_config(
                            config, versioned_content, self.auto_confirm
                        )
                        if result:
                            updated_configs.append(config.name)
                        else:
                            unchanged_configs.append(config.name)
                    else:
                        unchanged_configs.append(config.name)
                elif self.create_new_config(config, versioned_content, self.auto_confirm):
                    updated_configs.append(config.name)
                else:
                    unchanged_configs.append(config.name)
            else:
                # If remote fetch failed, report it
                failed_configs.append(config.name)

        return updated_configs, failed_configs, unchanged_configs

    def needs_update(self, config_path: Path) -> bool:
        """Check if a config file needs updating based on its embedded version."""
        if not config_path.exists():
            return True

        # Extract version from local config file
        local_version = self.get_local_version(config_path)

        # Get the latest version
        latest_version = self.get_latest_version()

        # If versions don't match, update is needed
        return not local_version or local_version != latest_version

    def get_local_version(self, config_path: Path) -> str | None:
        """Extract the version from a local config file."""
        if not config_path.exists():
            return None

        content = config_path.read_text()
        for line in content.splitlines():
            if "Config version:" in line and "auto-managed" in line:
                try:
                    return line.split("Config version:")[1].split("(auto-managed)")[0].strip()
                except IndexError:
                    pass
        return None

    def get_latest_version(self) -> str:
        """Get the latest config version based on the package version."""
        full_version = self.version_info.current or "dev"
        if full_version != "dev":
            # Split by dots and take first two components
            version_parts = full_version.split(".")
            if len(version_parts) >= 2:
                return f"{version_parts[0]}.{version_parts[1]}"
            return full_version
        return "dev"

    def add_version_to_content(self, content: str, filename: str) -> str:
        """Add version information to the content at download time."""
        suffix = Path(filename).suffix
        comment_start, comment_end = self.VERSION_COMMENT_FORMAT.get(suffix, ("# ", ""))

        # Use the latest version
        latest_ver = self.get_latest_version()
        version_line = f"{comment_start}Config version: {latest_ver} (auto-managed){comment_end}"

        # Strip any existing version lines
        lines = content.splitlines()
        cleaned_lines = [
            line for line in lines if "Config version:" not in line or "auto-managed" not in line
        ]

        # Count trailing blank lines in the original content and ensure at least one
        trailing_newlines = len(content) - len(content.rstrip("\n"))
        trailing_newlines = max(1, trailing_newlines)

        # Add version line, preserve trailing newlines, but ensure no double blank lines
        result = version_line + "\n" + "\n".join(cleaned_lines) + "\n" * trailing_newlines
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        return result

    def extract_version_from_file(self, file_path: Path) -> str | None:
        """Extract version information from a file."""
        if not file_path.exists():
            return None

        content = file_path.read_text()
        for line in content.splitlines():
            if "Config version:" in line and "auto-managed" in line:
                try:
                    return line.split("Config version:")[1].split("(auto-managed)")[0].strip()
                except IndexError:
                    pass
        return None

    def fetch_remote_content(self, config: ConfigFile) -> str | None:
        """Fetch content from remote URL. Returns None if the fetch fails."""
        try:
            response = requests.get(config.url)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            self.logger.warning("Failed to download %s from %s", config.name, config.url)
            return None

    def update_existing_config(self, config: ConfigFile, content: str, auto_confirm: bool) -> bool:
        """Update an existing config file if needed.

        Args:
            config: The config file to update.
            content: The new content to update the config file with (including version comment).
            auto_confirm: If True, skip the confirmation prompt and write the file directly.

        Returns:
            True if the file was updated, False otherwise.
        """
        current = config.path.read_text()
        local_version = self.get_local_version(config.path)
        latest_version = self.get_latest_version()

        # Get content without version lines for comparison
        current_lines = [
            line
            for line in current.splitlines()
            if "Config version:" not in line or "auto-managed" not in line
        ]
        content_lines = [
            line
            for line in content.splitlines()
            if "Config version:" not in line or "auto-managed" not in line
        ]

        # If only the version line is different, show a simplified message
        if current_lines == content_lines:
            if local_version != latest_version:
                if auto_confirm or confirm_action(
                    f"Update {config.name} config version from {local_version} to {latest_version}?",
                    default_to_yes=True,
                    prompt_color="yellow",
                ):
                    config.path.write_text(content)
                    self.logger.info(
                        "Updated %s config version from %s to %s.",
                        config.name,
                        local_version,
                        latest_version,
                    )
                    return True
                return False
            return False

        if not auto_confirm:
            show_diff(current, content, config.path.name)

        if auto_confirm or confirm_action(
            f"Update {config.name} config?", default_to_yes=True, prompt_color="yellow"
        ):
            config.path.write_text(content)
            self.logger.info("Updated %s config.", config.name)
            return True

        return False

    def create_new_config(self, config: ConfigFile, content: str, auto_confirm: bool) -> bool:
        """Create a new config file.

        Args:
            config: The config file to create.
            content: The content to write to the config file.
            auto_confirm: If True, skip the confirmation prompt and write the file directly.

        Returns:
            True if the file was updated, False otherwise.
        """
        if auto_confirm or confirm_action(
            f"Create new {config.name} config?", default_to_yes=True, prompt_color="green"
        ):
            config.path.write_text(content)
            self.logger.info("Created new %s config.", config.name)
            return True

        self.logger.debug("Skipped creation of %s config.", config.name)
        return False

    @property
    def first_time_setup(self) -> bool:
        """Check if this is a first-time setup (no configs exist yet)."""
        return not any(config.path.exists() for config in self.CONFIGS)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update config files from central repository")
    parser.add_argument("-y", action="store_true", help="update files without confirmation")
    return parser.parse_args()


def main() -> None:
    """Fetch and update the config files."""
    args = parse_args()
    CodeConfigs(skip_confirm=args.y)


if __name__ == "__main__":
    main()
