"""Download configs for coding tools and compare against local versions.

This script is designed to download configuration files for various coding tools (e.g., ruff, mypy)
to compare against files with the same name in the directory where the script is run. This is to
ensure that I always have the latest versions of my preferred configurations for all my projects.

Note that these config files live in the dsbin repository: https://github.com/dannystewart/dsbin

The script also saves the updated config files to the package root, which is the root of the dsbin
repository itself, thereby creating a virtuous cycle where the repo is always up-to-date with the
latest versions of the config files for other projects to pull from.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import requests
from polykit.cli import ArgParser, confirm_action
from polykit.formatters import color, show_diff
from polykit.log import Logician

from dsbin.files import FileManager

if TYPE_CHECKING:
    import argparse


@dataclass
class ConfigFile:
    """Represents a config file that can be updated from a remote source."""

    BASE_URL: ClassVar[str] = "https://raw.githubusercontent.com/dannystewart"
    REPO: ClassVar[str] = "dsbin"
    FOLDER: ClassVar[str] = "configs"

    name: str
    url: str = field(init=False)
    local_path: Path = field(init=False)
    post_update_command: str | list[str] | None = None

    def __post_init__(self):
        self.url = f"{self.BASE_URL}/{self.REPO}/refs/heads/main/{self.FOLDER}/{self.name}"
        self.local_path = Path.cwd() / self.name


class ConfigManager:
    """Manages downloading and updating config files from a remote repository."""

    CONFIGS: ClassVar[list[ConfigFile]] = [
        ConfigFile("ruff.toml"),
        ConfigFile("mypy.ini"),
        ConfigFile(".github/workflows/docs.yml"),
        ConfigFile(".github/workflows/python-publish.yml"),
        ConfigFile(".github/copilot-instructions.md"),
        ConfigFile("code-style.md"),
        ConfigFile(
            ".pre-commit-config.yaml",
            post_update_command=["pre-commit", "uninstall", "&&", "pre-commit", "install"],
        ),
    ]

    def __init__(self, no_confirm: bool = False):
        self.logger = Logician.get_logger()
        self.files = FileManager()
        self.no_confirm = no_confirm
        self.changes_made = set()

        # Determine if all configs should be created by checking if any exist locally
        self.should_create_all = not any(config.local_path.exists() for config in self.CONFIGS)

        if self.should_create_all:
            self.logger.debug(
                "No existing configs found; downloading and creating all available configs."
            )

    def update_configs(self) -> None:
        """Pull down latest configs from repository, updating local copies."""
        for config in self.CONFIGS:
            remote_content = self.fetch_remote_content(config)
            if not remote_content:
                self.logger.error(
                    "Failed to update %s config as it was not available.", config.name
                )
                continue

            if self.process_config(config, remote_content):
                self.changes_made.add(config.name)
                # Run post-update command if specified and file was updated
                if config.post_update_command:
                    self.run_post_update_command(config)

        # Report unchanged configs
        if unchanged := [c.name for c in self.CONFIGS if c.name not in self.changes_made]:
            unchanged.sort()
            self.logger.info("No changes made for:\n- %s", "\n- ".join(unchanged))

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
        if "/" in config.name or "\\" in config.name:  # Ensure parent directories exist
            parent_dir = config.local_path.parent
            if not parent_dir.exists():
                if (
                    self.no_confirm
                    or self.should_create_all
                    or confirm_action(
                        f"Directory {parent_dir} does not exist. Create?", default_to_yes=True
                    )
                ):
                    parent_dir.mkdir(parents=True, exist_ok=True)
                    self.logger.info("Created directory %s", parent_dir)
                else:
                    self.logger.info(
                        "Skipping %s as parent directory creation was declined.", config.name
                    )
                    return False

        if config.local_path.exists():
            local_content = config.local_path.read_text()
            if local_content == remote_content:
                return False

            if not self.no_confirm:
                show_diff(local_content, remote_content, config.local_path.name)
                if not confirm_action(f"Update {config.name} config?", default_to_yes=True):
                    return False
        elif not (
            self.no_confirm
            or self.should_create_all
            or confirm_action(
                color(f"{config.name} config does not exist locally. Create?", "yellow"),
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

    def run_post_update_command(self, config: ConfigFile) -> None:
        """Run post-update command for a config file."""
        if config.post_update_command is None:
            return

        try:
            cmd = config.post_update_command
            self.logger.info("Running post-update command for %s.", config.name)

            # Special handling for pre-commit
            if config.name == ".pre-commit-config.yaml" and not is_git_repository():
                self.logger.warning(
                    "Skipping pre-commit hook installation as this is not a Git repository."
                )
                return

            # Convert list to string if needed and run the command
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            self.logger.debug("Executing: %s", cmd_str)
            subprocess.run(cmd_str, shell=True, check=True)

            self.logger.info("Post-update command for %s completed successfully!", config.name)

        except subprocess.CalledProcessError as e:
            self.logger.error(
                "Post-update command for %s failed. Exit code: %d.", config.name, e.returncode
            )
        except Exception as e:
            self.logger.error("Failed to run post-update command for %s: %s", config.name, str(e))


def is_git_repository() -> bool:
    """Check if the current directory is in a Git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = ArgParser(description="Update config files from central repository")
    parser.add_argument("-y", action="store_true", help="update files without confirmation")
    parser.add_argument(
        "-f", "--force", action="store_true", help="force update even if not in a Git repository"
    )
    return parser.parse_args()


def main() -> None:
    """Fetch and update the config files."""
    args = parse_args()

    # Check if we're in a Git repository
    if not is_git_repository() and not args.force:
        logger = Logician.get_logger()
        logger.error("This is intended to run inside of a Git repository. Use --force to override.")
        return

    manager = ConfigManager(no_confirm=args.y)
    manager.update_configs()


if __name__ == "__main__":
    main()
