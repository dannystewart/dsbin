"""This file contains the ConfigFile dataclass and a list of ConfigFile objects that contain the
paths and URLs to the reference files used when running the script.

Note that these config files live in the dsbin repository: https://github.com/dannystewart/dsbin
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final


@dataclass
class ConfigFile:
    """Represents a config file that can be updated from a remote source.

    Args:
        name: The name of the config file.
        url: The URL to the remote source.
        local_path: The path to the config file in the local package root.
        remote_path: The path to the config file in the repo.
    """

    name: str
    url: str
    local_path: Path
    remote_path: Path

    def __post_init__(self):
        # We're saving the updated configs to ourself, so we need to go up the tree
        this_script = Path(__file__)  # This assumes we're at src/dsbin/code_configs/config_files.py
        code_configs_folder = this_script.parent  # src/dsbin/code_configs
        dsbin_root = code_configs_folder.parent  # src/dsbin
        src_root = dsbin_root.parent  # src
        package_root = src_root.parent  # package root

        self.remote_path = package_root / self.local_path.name
        self.remote_path.parent.mkdir(exist_ok=True)


CONFIGS: Final[list[ConfigFile]] = [
    ConfigFile(
        name="ruff",
        url="https://raw.githubusercontent.com/dannystewart/dsbin/refs/heads/main/ruff.toml",
        local_path=Path("ruff.toml"),
        remote_path=Path(),
    ),
    ConfigFile(
        name="mypy",
        url="https://raw.githubusercontent.com/dannystewart/dsbin/refs/heads/main/mypy.ini",
        local_path=Path("mypy.ini"),
        remote_path=Path(),
    ),
]
