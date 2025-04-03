from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterator

T = TypeVar("T")


class DatabaseError(Exception):
    """Base exception for database operations."""


@dataclass
class QueryResult[T]:
    """Represent the result of a database operation."""

    data: T | None
    affected_rows: int = 0

    def __bool__(self) -> bool:
        """Allow direct boolean testing of result."""
        return self.data is not None

    def __getitem__(self, key: str) -> Any:
        """Allow direct dictionary-style access to data.

        Raises:
            KeyError: If no data is available.
            TypeError: If data is not a dictionary.
        """
        if not self.data:
            msg = f"No data available to access key '{key}'"
            raise KeyError(msg)
        if not isinstance(self.data, dict):
            msg = "Data is not a dictionary"
            raise TypeError(msg)
        return self.data[key]

    def get(self, key: str, default: Any | None = None) -> Any:
        """Dictionary-style get with default value."""
        try:
            return self[key]
        except (KeyError, TypeError):
            return default

    def __iter__(self) -> Iterator[Any]:
        """Allow direct iteration when data is a list.

        Raises:
            TypeError: If data is not a list.
        """
        if self.data is None:
            return iter([])
        if not isinstance(self.data, list):
            msg = "Data is not a list."
            raise TypeError(msg)
        return iter(self.data)

    def __len__(self) -> int:
        """Return length of data if it's a list, or 0 if None.

        Raises:
            TypeError: If data is not a list.
        """
        if self.data is None:
            return 0
        if not isinstance(self.data, list):
            msg = "Data is not a list."
            raise TypeError(msg)
        return len(self.data)
