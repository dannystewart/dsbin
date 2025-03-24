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

import requests

from dsbase.files import FileManager
from dsbase.log import LocalLogger
from dsbase.shell import confirm_action
from dsbase.text.diff import show_diff

from dsbin.configs.config_file import CONFIGS, ConfigFile

logger = LocalLogger().get_logger()
files = FileManager()


def update_config_file(config_file: ConfigFile, new_content: str, for_repo: bool = False) -> bool:
    """Update a config file if changes are detected.

    Args:
        config_file: The config file to be updated.
        new_content: The new config file's content.
        for_repo: Whether this is the version that lives in the repo (as opposed to local).

    Returns:
        True if the file was updated, False otherwise.
    """
    target = config_file.remote_path if for_repo else config_file.local_path
    location = "repo" if for_repo else "local"

    if not target.exists():
        target.write_text(new_content)
        logger.info("Created new %s %s config at %s.", location, config_file.name, target)
        return True

    current = target.read_text()
    if current == new_content:
        return False

    show_diff(current, new_content, target.name)
    if confirm_action(f"Update {location} {config_file.name} config?", prompt_color="yellow"):
        target.write_text(new_content)
        return True

    return False


def handle_local_update(config: ConfigFile, remote_content: str, auto_update: bool) -> bool:
    """Handle the updating an existing local config file.

    Args:
        config: The config file to be updated.
        remote_content: The remote file's content.
        auto_update: Whether to update all files without showing diffs and confirming.

    Returns:
        True if the file was updated, False otherwise.
    """
    current_content = config.local_path.read_text()
    if current_content == remote_content:
        return False

    if not auto_update:
        show_diff(remote_content, current_content, config.local_path.name)
    if auto_update or confirm_action(f"Update local {config.name} config?", default_to_yes=True):
        config.local_path.write_text(remote_content)
        logger.info("Updated %s config.", config.name)
        return True

    return False


def handle_config_update(
    config: ConfigFile,
    remote_content: str,
    auto_update: bool = False,
    auto_create: bool = False,
) -> bool:
    """Handle the updating or creation of a single config file.

    Args:
        config: The config file to be updated.
        remote_content: The content of the remote file.
        auto_update: Whether to update all files without showing diffs and confirming.
        auto_create: Whether to create non-existing config files without prompting.

    Returns:
        True if the file was updated or created, False otherwise.
    """
    if config.local_path.exists():
        return handle_local_update(config, remote_content, auto_update)

    # Create the file if the user confirms or if auto_create or auto_update is True
    confirm_message = f"{config.name} config does not exist locally. Create?"
    if auto_create or auto_update or confirm_action(confirm_message, default_to_yes=True):
        config.local_path.write_text(remote_content)
        logger.info("Created new %s config.", config.name)
        return True

    logger.debug("Skipped creation of %s config.", config.name)
    return False


def update_configs(auto_update: bool = False) -> None:
    """Pull down latest configs from repository, updating both local and repo copies.

    Args:
        auto_update: Whether to update all files without showing diffs and confirming.
    """
    changes_made = set()

    # Check if any config files exist at all
    any_config_exists = any(config.local_path.exists() for config in CONFIGS)
    should_create_all = not any_config_exists

    if should_create_all:
        logger.debug("No existing configs found; downloading and creating all available configs.")

    for config in CONFIGS:
        try:
            response = requests.get(config.url)
            response.raise_for_status()
            remote_content = response.text

            # Always update the repo copy first as this is our fallback
            config.remote_path.parent.mkdir(exist_ok=True)
            config.remote_path.write_text(remote_content)

            if handle_config_update(
                config, remote_content, auto_update=auto_update, auto_create=should_create_all
            ):
                changes_made.add(config.name)

        except requests.RequestException:
            if config.remote_path.exists() and config.local_path.exists():
                files.copy(config.remote_path, config.local_path)
                logger.warning("Failed to download %s config, copied from repo.", config.name)
            elif (
                config.local_path.exists()
                or should_create_all
                or (
                    not auto_update
                    and confirm_action(
                        f"Create {config.name} config from repo?", default_to_yes=True
                    )
                )
            ):
                if config.remote_path.exists():
                    files.copy(config.remote_path, config.local_path)
                    logger.info("Created %s config from repo.", config.name)
                else:
                    logger.error("Failed to update %s config.", config.name)
            else:
                logger.debug("Skipping creation of %s config.", config.name)

    unchanged = [c.name for c in CONFIGS if c.name not in changes_made]
    if unchanged:
        logger.info("No changes needed for: %s", ", ".join(unchanged))


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update config files from central repository")
    parser.add_argument("-y", action="store_true", help="update files without confirmation")
    return parser.parse_args()


def main() -> None:
    """Fetch and update the config files."""
    args = parse_args()
    update_configs(auto_update=args.y)


if __name__ == "__main__":
    main()
