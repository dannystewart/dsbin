from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILE = "configs.yaml"


@dataclass
class Config:
    """Dataclass to hold configuration parameters."""

    type: str = "default"
    min_length: int = 3
    max_length: int = 6
    start_max: int = 8
    base_dir: list[str] = field(default_factory=list)
    file_extensions: list[str] = field(default_factory=list)
    sort_by: str = "none"
    excluded_dirs: list[str] = field(default_factory=list)
    cache_seconds: int = 7200
    pre_command: str | None = None
    search_subdirectory: str | None = None
    package_extensions: list[str] = field(default_factory=list)
    max_files_per_folder: int | None = None


@dataclass
class FileMetadata:
    """Dataclass to hold file metadata."""

    title: str
    subtitle: str
    time: float


class ConfigHandler:
    """Class to handle config loading and merging."""

    def __init__(self, config_name: str):
        self.config_name = config_name
        self.config_data = self._load_config()
        self.config = self._parse_config(self.config_data)

    def _load_config(self) -> dict[str, Any]:
        """Load the configuration from the YAML file, merging with default values.

        Raises:
            ValueError: If the configuration is not found.
        """
        with Path(CONFIG_FILE).open(encoding="utf-8") as file:
            configs = yaml.safe_load(file)

        if self.config_name == "default":
            msg = "Cannot use 'default' config. Please specify a specific configuration."
            raise ValueError(msg)

        default_config = configs.get("default", {})

        # Handle nested keys
        parts = self.config_name.split(".")
        specific_config = configs
        for part in parts:
            specific_config = specific_config.get(part)
            if specific_config is None:
                msg = f"Configuration '{self.config_name}' not found."
                raise ValueError(msg)

        if not isinstance(specific_config, dict):
            msg = f"Configuration '{self.config_name}' is not a valid configuration object."
            raise ValueError(msg)

        merged_config = {**default_config, **specific_config}

        # Ensure base_dir is always a list
        if isinstance(merged_config.get("base_dir"), str):
            merged_config["base_dir"] = [merged_config["base_dir"]]

        return merged_config

    def _parse_config(self, config_data: dict[str, Any]) -> Config:
        valid_fields = {f.name for f in fields(Config)}
        filtered_config = {k: v for k, v in config_data.items() if k in valid_fields}
        return Config(**filtered_config)

    def _load_configs_from_file(self, config_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load the configurations from the YAML file.

        Raises:
            ValueError: If the configuration is not found.
        """
        with Path(CONFIG_FILE).open(encoding="utf-8") as file:
            configs = yaml.safe_load(file)

        default_config = configs.get("default", {})

        # Handle nested keys
        parts = config_name.split(".")
        specific_config = configs
        for part in parts:
            specific_config = specific_config.get(part)
            if specific_config is None:
                msg = f"Configuration '{config_name}' not found."
                raise ValueError(msg)

        if not isinstance(specific_config, dict):
            msg = f"Configuration '{config_name}' is not a valid configuration object."
            raise ValueError(msg)

        return default_config, specific_config
