"""Plugin registry for data source plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from dsbin.workcalc.plugin import DataSourcePlugin


class PluginRegistry:
    """Registry for data source plugins."""

    _plugins: ClassVar[dict[str, type[DataSourcePlugin]]] = {}

    @classmethod
    def register(cls, plugin_class: type[DataSourcePlugin]) -> None:
        """Register a plugin class."""
        cls._plugins[plugin_class.source_name] = plugin_class

    @classmethod
    def get_plugin(cls, source_name: str) -> type[DataSourcePlugin] | None:
        """Get a plugin class by source name."""
        return cls._plugins.get(source_name)

    @classmethod
    def get_all_plugins(cls) -> Iterator[type[DataSourcePlugin]]:
        """Get all registered plugin classes."""
        return iter(cls._plugins.values())

    @classmethod
    def get_source_names(cls) -> list[str]:
        """Get all registered source names."""
        return list(cls._plugins.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered plugins (useful for testing)."""
        cls._plugins.clear()
