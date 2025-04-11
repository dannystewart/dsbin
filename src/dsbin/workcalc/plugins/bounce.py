from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from polykit.files import PolyFile
from polykit.log import PolyLog

from dsbin.workcalc.data import WorkItem
from dsbin.workcalc.plugin import DataSourcePlugin

if TYPE_CHECKING:
    from collections.abc import Iterator
    from logging import Logger


@dataclass
class BounceDataSource(DataSourcePlugin):
    """Logic Pro bounce file data source."""

    BOUNCE_EXTENSIONS: ClassVar[list[str]] = ["wav", "m4a"]

    bounce_dir: str | Path
    logger: Logger = field(init=False)

    def __post_init__(self):
        self.directory = Path(self.bounce_dir)
        self.logger = PolyLog.get_logger()

    @property
    def source_name(self) -> str:
        """Name of this data source type."""
        return "logic"

    def validate_source(self) -> bool:
        """Verify the directory exists and contains audio files."""
        if not self.directory.is_dir():
            return False

        # Check for at least one audio file
        try:
            next(self._find_audio_files())
            return True
        except StopIteration:
            return False

    def get_work_items(self) -> Iterator[WorkItem]:
        """Get all bounce files as work items.

        Yields:
            WorkItem: A work item representing a bounce file.
        """
        for file_path in self._find_audio_files():
            try:
                ctime, mtime = PolyFile.get_timestamps(file_path)
                # Parse the creation timestamp
                timestamp = self._parse_timestamp(ctime)

                yield WorkItem(
                    timestamp=timestamp,
                    source_path=file_path,
                    description=file_path.name,
                    metadata={
                        "modified": self._parse_timestamp(mtime),
                        "size": file_path.stat().st_size,
                    },
                )
            except (ValueError, OSError) as e:  # Log error but continue
                self.logger.error("Error processing %s: %s", file_path, str(e))
                continue

    def _find_audio_files(self) -> Iterator[Path]:
        """Find all audio files in the directory."""
        files = PolyFile.list(
            self.directory,
            extensions=self.BOUNCE_EXTENSIONS,
            recursive=True,
            sort_key=lambda x: x.stat().st_mtime,
        )
        return (Path(f) for f in files)

    @staticmethod
    def _parse_timestamp(timestamp: str) -> datetime:
        """Parse the timestamp string returned by get_timestamps.

        Raises:
            ValueError: If the timestamp can't be parsed.
        """
        formats = [
            "%m/%d/%Y %I:%M:%S %p",  # 12-hour format with AM/PM
            "%m/%d/%Y %H:%M:%S",  # 24-hour format
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp, fmt)  # noqa: DTZ007
            except ValueError:
                continue

        msg = f"Unable to parse timestamp: {timestamp}"
        raise ValueError(msg)
