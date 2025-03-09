from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from .file_type_handler import FileTypeHandler

if TYPE_CHECKING:
    from config_handler import Config


class LogicFileHandler(FileTypeHandler):
    """Class to handle Logic project and bounce metadata."""

    def get_metadata(
        self, file_path: Path, base_dir: Path | list[Path], config: Config
    ) -> tuple[str, str]:
        """Get the metadata for a Logic project or bounce file."""
        if config.type == "logic_projects":
            title = self._get_logic_project_title(file_path)
        elif config.type == "logic_bounces":
            title = self._get_logic_bounce_title(file_path)
        else:
            title = file_path.name

        if isinstance(base_dir, list):
            # If multiple base directories, find the correct one
            for dir_path in base_dir:
                try:
                    relative_path = file_path.relative_to(dir_path)
                    break
                except ValueError:
                    continue
        else:
            relative_path = file_path.relative_to(base_dir)

        subtitle = str(relative_path.parent).replace("/Bounces", "").replace("/", " ≫ ")

        return title, subtitle

    def _get_logic_project_title(self, file_path: Path) -> str:
        """Get the display title for a Logic project search result.

        If it's in a folder that doesn't contain an 'Audio Files' folder, it's in a subfolder, so
        prepend the name of the parent folder.
        """
        project_name = file_path.stem
        project_dir = file_path.parent
        parent_dir = project_dir.parent

        if "Audio Files" in [item.name for item in parent_dir.iterdir()]:
            parent_folder_name = project_dir.name
            return f"{parent_folder_name} ≫ {project_name}"
        return project_name

    def _get_logic_bounce_title(self, file_path: Path) -> str:
        """Get the display title for a Logic bounce search result.

        If it's in a subfolder of the 'Bounces' folder, prepend the name of the parent folder, and
        rename for readability.
        """
        path_parts = file_path.parts
        try:
            bounces_index = path_parts.index("Bounces") + 1
            title_parts = os.path.sep.join(path_parts[bounces_index:])
            title = Path(title_parts).stem
            return title.replace(os.path.sep, " ≫ ").replace("_Older", "Older Bounces")
        except ValueError:
            return file_path.name
