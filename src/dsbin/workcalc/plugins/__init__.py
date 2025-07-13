from __future__ import annotations

from dsbin.workcalc.plugin_registry import PluginRegistry

from .bounce import BounceDataSource
from .git import GitDataSource


def initialize_plugins() -> None:
    """Initialize and register all available plugins."""
    PluginRegistry.register(BounceDataSource)
    PluginRegistry.register(GitDataSource)
