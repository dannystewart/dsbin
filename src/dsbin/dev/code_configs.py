from __future__ import annotations

import argparse
import shutil
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import requests

from dsbase.diff import show_diff
from dsbase.log import LocalLogger
from dsbase.shell import confirm_action

logger = LocalLogger().get_logger(__name__)


@dataclass
class ConfigFile:
    """Represents a config file that can be updated from a remote source."""

    name: str
    url: str
    local_path: Path
    package_path: Path

    def __post_init__(self) -> None:
        self.package_path = Path(__file__).parent / "configs" / self.local_path.name
        self.package_path.parent.mkdir(exist_ok=True)


CONFIGS: Final[list[ConfigFile]] = [
    ConfigFile(
        name="ruff",
        url="https://raw.githubusercontent.com/dannystewart/dsbase/refs/heads/main/src/dsbase/configs/configs/ruff.toml",
        local_path=Path("ruff.toml"),
        package_path=Path(),
    ),
    ConfigFile(
        name="mypy",
        url="https://raw.githubusercontent.com/dannystewart/dsbase/refs/heads/main/src/dsbase/configs/configs/mypy.ini",
        local_path=Path("mypy.ini"),
        package_path=Path(),
    ),
]


def parse_args() -> Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update config files from central repository")
    parser.add_argument(
        "-u", "--update-only", action="store_true", help="only update existing, don't create new"
    )
    parser.add_argument(
        "-y", "--yes", action="store_true", help="update all configs without confirmation"
    )
    return parser.parse_args()


def update_config_file(config: ConfigFile, content: str, is_package: bool = False) -> bool:
    """Update a config file if changes are detected.

    Args:
        config: The config file to update.
        content: The new content.
        is_package: Whether this is the package version (as opposed to local).

    Returns:
        Whether the file was updated.
    """
    target = config.package_path if is_package else config.local_path
    location = "package" if is_package else "local"

    if not target.exists():
        target.write_text(content)
        logger.info("Created new %s %s config at %s.", location, config.name, target)
        return True

    current = target.read_text()
    if current == content:
        return False

    show_diff(current, content, target.name)
    if confirm_action(f"Update {location} {config.name} config?", prompt_color="yellow"):
        target.write_text(content)
        return True

    return False


def handle_local_update(config: ConfigFile, remote_content: str, auto_confirm: bool) -> bool:
    """Handle updating an existing local config file."""
    current_content = config.local_path.read_text()
    if current_content == remote_content:
        return False

    if not auto_confirm:
        show_diff(remote_content, current_content, config.local_path.name)
    if auto_confirm or confirm_action(f"Update local {config.name} config?", default_to_yes=True):
        config.local_path.write_text(remote_content)
        logger.info("Updated %s config.", config.name)
        return True

    return False


def handle_config_update(
    config: ConfigFile, remote_content: str, *, update_only: bool, auto_confirm: bool
) -> bool:
    """Handle updating or creating a single config file."""
    if config.local_path.exists():
        return handle_local_update(config, remote_content, auto_confirm)
    if not update_only:
        config.local_path.write_text(remote_content)
        logger.info("Created new %s config.", config.name)
        return True
    logger.debug("Skipping creation of %s config (update-only mode).", config.name)
    return False


def update_configs(*, update_only: bool = False, auto_confirm: bool = False) -> None:
    """Pull down latest configs from GitLab, updating both local and package copies.

    Args:
        update_only: Only update existing config files, don't create new ones.
        auto_confirm: Automatically confirm all updates without prompting.
    """
    changes_made = set()

    for config in CONFIGS:
        try:
            response = requests.get(config.url)
            response.raise_for_status()
            remote_content = response.text

            # Always update the package copy first as this is our fallback
            config.package_path.parent.mkdir(exist_ok=True)
            config.package_path.write_text(remote_content)

            if handle_config_update(
                config, remote_content, update_only=update_only, auto_confirm=auto_confirm
            ):
                changes_made.add(config.name)

        except requests.RequestException:
            if config.package_path.exists() and config.local_path.exists():
                shutil.copy(config.package_path, config.local_path)
                logger.warning(
                    "Failed to download %s config, copied from package version.", config.name
                )
            elif not update_only or config.local_path.exists():
                logger.error("Failed to update %s config.", config.name)
            else:
                logger.debug("Skipping creation of %s config (update-only mode).", config.name)

    unchanged = [c.name for c in CONFIGS if c.name not in changes_made]
    if unchanged:
        logger.info("No changes needed for: %s", ", ".join(unchanged))


def main() -> None:
    """Update the configs."""
    args = parse_args()
    update_configs(update_only=args.update_only, auto_confirm=args.yes)


if __name__ == "__main__":
    main()
