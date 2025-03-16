from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from dsbase.log import LocalLogger

if TYPE_CHECKING:
    from logging import Logger


class Action(Enum):
    """Valid actions for the Prism controller."""

    START = auto()
    RESTART = auto()
    STOP = auto()
    LOGS = auto()
    SYNC = auto()

    @classmethod
    def from_str(cls, value: str) -> Action:
        """Create an Action from a string value."""
        try:
            return cls[value.upper()]
        except KeyError:
            return cls.LOGS  # default to logs


@dataclass(frozen=True)
class PrismConfig:
    """Configuration for Prism controller operations."""

    action: Action
    on_dev: bool
    on_all: bool
    logger: Logger

    @classmethod
    def from_args(cls, args: set[str], logger: Logger | None = None) -> PrismConfig:
        """Create a PrismConfig from command-line arguments.

        Args:
            args: Set of lowercase argument strings.
            logger: Optional logger instance to use for internal logging.

        Returns:
            Configured PrismConfig instance.
        """
        logger = logger or LocalLogger().get_logger()

        # Define valid options
        actions = {name.lower() for name in Action.__members__}
        modifiers = {"dev", "all"}

        # Find the action (default to logs if none specified)
        action_str = next((arg for arg in args if arg in actions), "logs")
        action = Action.from_str(action_str)

        # Check for modifiers
        is_dev = "dev" in args
        is_all = "all" in args

        # Validate combinations
        if is_dev and is_all:
            logger.error("Cannot specify both 'dev' and 'all' at the same time")
            sys.exit(1)

        # Check for unknown arguments
        valid_args = actions | modifiers
        unknown_args = args - valid_args
        if unknown_args:
            logger.error("Unknown arguments: %s", ", ".join(unknown_args))
            sys.exit(1)

        return cls(action=action, on_dev=is_dev, on_all=is_all, logger=logger)
