from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .file_type_handler import FileTypeHandler

if TYPE_CHECKING:
    from config_handler import Config


class DefaultFileHandler(FileTypeHandler):
    """Default file handler for files that don't have a specific handler."""

    def get_metadata(
        self,
        file_path: Path,
        base_dir: Path | list[Path],
        config: Config,  # noqa: ARG002
    ) -> tuple[str, str]:
        """Get the title and subtitle for a file."""
        path = Path(file_path)
        title = path.name

        # Handle both string and list cases for base_dir
        base_dir_list = [base_dir] if isinstance(base_dir, Path) else base_dir

        # Find the correct base directory for this file
        expanded_base_dirs = [Path(d).expanduser() for d in base_dir_list]
        rel_dir = next((d for d in expanded_base_dirs if Path(file_path).is_relative_to(d)), None)

        rel_path = Path(file_path).relative_to(rel_dir) if rel_dir else Path(file_path)

        subtitle = str(rel_path.parent)
        return title, subtitle
