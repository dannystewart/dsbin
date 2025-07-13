from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterator

    from dsbin.workcalc.data import WorkItem


class DataSourcePlugin(ABC):
    """Abstract base class for work data source plugins."""

    # Class attributes that must be defined by subclasses
    source_name: ClassVar[str]
    item_name: ClassVar[str]
    help_text: ClassVar[str]
    description: ClassVar[str]

    @abstractmethod
    def validate_source(self) -> bool:
        """Verify the data source is valid and accessible."""
        msg = "Subclasses must implement validate_source"
        raise NotImplementedError(msg)

    @abstractmethod
    def get_work_items(self) -> Iterator[WorkItem]:
        """Retrieve work items from the data source."""
        msg = "Subclasses must implement get_work_items"
        raise NotImplementedError(msg)

    @classmethod
    @abstractmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        """Add source-specific arguments to the argument parser."""
        msg = "Subclasses must implement add_arguments"
        raise NotImplementedError(msg)

    @classmethod
    @abstractmethod
    def from_args(cls, args: argparse.Namespace) -> DataSourcePlugin:
        """Create an instance from parsed arguments."""
        msg = "Subclasses must implement from_args"
        raise NotImplementedError(msg)
