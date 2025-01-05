from __future__ import annotations

import subprocess
from datetime import datetime
from typing import TYPE_CHECKING

from .plugin import DataSourcePlugin
from .work_item import WorkItem

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class GitDataSource(DataSourcePlugin):
    """Git repository data source."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path

    @property
    def source_name(self) -> str:
        """Name of this data source type."""
        return "git"

    def validate_source(self) -> bool:
        """Verify that the path is a git repository."""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def get_work_items(self) -> Iterator[WorkItem]:
        """Get all commits as work items.

        Yields:
            WorkItem: A work item representing a commit.

        Raises:
            RuntimeError: If the current directory is not a git repository.
        """
        try:
            # Get commit timestamps and messages
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--format=%aI%x00%H%x00%s",  # ISO8601 timestamp, hash, and subject
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            msg = "Failed to get git commits"
            raise RuntimeError(msg) from e

        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            try:
                timestamp_str, commit_hash, message = line.split("\0")
                timestamp = datetime.fromisoformat(timestamp_str.strip())

                yield WorkItem(
                    timestamp=timestamp,
                    source_path=self.repo_path,
                    description=message,
                    metadata={
                        "hash": commit_hash,
                    },
                )
            except ValueError as e:
                # Log error but continue processing other commits
                print(f"Error parsing commit: {e}")  # TODO: Use logger
                continue
