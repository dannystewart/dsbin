from __future__ import annotations

from typing import TYPE_CHECKING

from .default_file_handler import DefaultFileHandler
from .logic_file_handler import LogicFileHandler

if TYPE_CHECKING:
    from .file_type_handler import FileTypeHandler


class HandlerFactory:
    """Factory class to get the appropriate file handler based on the file type."""

    @staticmethod
    def get_handler(file_type: str) -> FileTypeHandler:
        """Get the appropriate file handler based on the file type."""
        if file_type.startswith("logic"):
            return LogicFileHandler()
        return DefaultFileHandler()
