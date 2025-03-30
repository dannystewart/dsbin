from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from dsbin.workcalc.data import WorkItem


class DataSourcePlugin(ABC):
    """Abstract base class for work data source plugins."""

    @abstractmethod
    def validate_source(self) -> bool:
        """Verify the data source is valid and accessible."""
        ...

    @abstractmethod
    def get_work_items(self) -> Iterator[WorkItem]:
        """Retrieve work items from the data source."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of this data source type."""
        ...
