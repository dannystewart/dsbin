from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from config_handler import Config


class FileTypeHandler(ABC):
    """Abstract base class to handle metadata for different file types."""

    @abstractmethod
    def get_metadata(
        self,
        file_path: Path,
        base_dir: Path | list[Path],
        config: Config,
    ) -> tuple[str, str]:
        """Get the metadata for a specific file type."""
        raise NotImplementedError
