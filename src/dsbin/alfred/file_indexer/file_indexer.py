#!/usr/bin/env python3

"""
Alfred Script Filter that searches for files based on configurations specified in a YAML file.
It supports various file types, sorting methods, and can execute pre-commands before searching.

This Script Filter requires Alfred 5.5 or higher, and should be used with 'Alfred filters results'
enabled in the workflow with one of the 'Word matching' match modes. Results will be cached and
refreshed as specified in the config unless changes are detected. The 'loosereload' option attempts
to load the cache first and refresh in the background to minimize the delay in showing results.

Usage:
    CONFIG_NAME="config_name" /usr/bin/python3 ./file_indexer.py

Where "config_name" is the name of the configuration in the YAML file.

Alfred Script Filter reference: https://www.alfredapp.com/help/workflows/inputs/script-filter/
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from typing import Any

from config_handler import ConfigHandler, FileMetadata
from file_handlers.handler_factory import HandlerFactory
from fuzzy_matcher import FuzzyMatcher

CONFIG_FILE = "configs.yaml"


class FileIndexer:
    """Class to handle file indexing process."""

    def __init__(self, config_name: str):
        self.config_handler = ConfigHandler(config_name)
        self.config = self.config_handler.config
        self.fuzzy_matcher = FuzzyMatcher(self.config)
        self.file_handler = HandlerFactory.get_handler(self.config.type)

    def index_files(self) -> list[dict[str, Any]]:
        """Index files in the specified directories."""
        results = []
        for base_dir in self.config.base_dir:
            results.extend(self._index_directory(base_dir))
        return (
            sorted(results, key=lambda x: -x["time"]) if self.config.sort_by != "none" else results
        )

    def _index_directory(self, base_dir: str) -> list[dict[str, Any]]:
        results = []
        base_dir = os.path.expanduser(base_dir)
        search_subdirectory = self.config.search_subdirectory
        files_per_folder = defaultdict(list)

        for root, dirs, files in os.walk(base_dir):
            # Skip directories that don't contain the search_subdirectory if it's specified
            if search_subdirectory and search_subdirectory not in root.split(os.sep):
                continue

            dirs[:] = [d for d in dirs if d not in self.config.excluded_dirs]

            folder_files = []

            # Check for package-type files in directories
            if self.config.package_extensions:
                folder_files.extend(
                    self._process_files_in_directory(
                        root, dirs, self.config.package_extensions, base_dir
                    )
                )

            # Check regular files
            if self.config.file_extensions:
                folder_files.extend(
                    self._process_files_in_directory(
                        root, files, self.config.file_extensions, base_dir
                    )
                )

            # Sort folder files based on the sort criteria
            folder_files.sort(key=lambda x: -x["time"])

            # Limit the number of files per folder if max_files_per_folder is set
            if self.config.max_files_per_folder is not None:
                folder_files = folder_files[: self.config.max_files_per_folder]

            files_per_folder[root].extend(folder_files)

        # Sort folders by depth (shallowest first)
        sorted_folders = sorted(
            files_per_folder.keys(), key=lambda x: self._get_folder_depth(x, base_dir)
        )

        # Flatten the dictionary of folder files into a single list, maintaining folder order
        for folder in sorted_folders:
            results.extend(files_per_folder[folder])

        return results

    def _process_files_in_directory(
        self, root: str, names: list[str], extensions: list[str], base_dir: str
    ) -> list[dict[str, Any]]:
        """Process files or directories that match the given extensions."""
        processed_files = []
        for name in names:
            if any(name.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, name)
                processed_files.append(self._process_file(file_path, base_dir))
        return processed_files

    def _get_folder_depth(self, folder: str, base_dir: str) -> int:
        """Calculate the depth of a folder relative to the base directory."""
        return len(os.path.relpath(folder, base_dir).split(os.sep))

    def get_file_metadata(self, file_path: str, base_dir: str) -> FileMetadata:
        """Get the desired title, subtitle, and modification time for a file."""
        if hasattr(self.file_handler, "get_metadata"):
            title, subtitle = self.file_handler.get_metadata(file_path, base_dir, self.config)
        else:
            title = os.path.basename(file_path)
            subtitle = os.path.relpath(os.path.dirname(file_path), base_dir)
        time = self._get_file_time(file_path)
        return FileMetadata(title, subtitle, time)

    def _get_file_time(self, file_path: str) -> float:
        if self.config.sort_by == "mtime":
            return os.path.getmtime(file_path)
        if self.config.sort_by == "ctime":
            return os.path.getctime(file_path)
        return 0

    def _process_file(self, file_path: str, base_dir: str) -> dict[str, Any]:
        """Process a file and return its metadata in a format suitable for Alfred."""
        metadata = self.get_file_metadata(file_path, base_dir)
        match_strings = self.fuzzy_matcher.generate_match_strings(metadata.title)
        return {
            "uid": file_path,
            "type": "file",
            "title": metadata.title,
            "subtitle": metadata.subtitle,
            "arg": file_path,
            "autocomplete": metadata.title,
            "match": match_strings,
            "icon": {"type": "fileicon", "path": file_path},
            "time": metadata.time,
        }

    def execute_pre_command(self) -> None:
        """Execute the pre-command, redirecting output to prevent interference with Alfred's JSON parsing."""
        command = self.config.pre_command
        if not command:
            return
        try:
            with open(os.devnull, "w") as devnull:
                subprocess.run(command, shell=True, check=True, stdout=devnull, stderr=devnull)
        except subprocess.CalledProcessError as e:
            print(f"Pre-command failed: {e}", file=sys.stderr)  # noqa: T201

    def get_file_list(self) -> None:
        """Find and return files according to the selected configuration."""
        self.execute_pre_command()
        result = self.index_files()

        json_output = json.dumps(
            {
                "cache": {
                    "seconds": self.config.cache_seconds,
                    "loosereload": "true",
                },
                "items": result,
                "skipknowledge": "true",
            }
        )
        sys.stdout.write(json_output)


if __name__ == "__main__":
    config_name = os.getenv("CONFIG_NAME", "default")
    FileIndexer(config_name).get_file_list()
