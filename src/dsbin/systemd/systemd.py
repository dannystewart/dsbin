from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


@dataclass
class SystemdServiceTemplate:
    """Configuration for a systemd service."""

    name: str
    description: str
    command: list[str]
    schedule: str  # e.g., "15min" or "1h"
    boot_delay: str = "5min"
    user: str = "root"
    after_targets: list[str] | None = None

    def generate_service_file(self) -> str:
        """Generate the content for the systemd service file."""
        after = " ".join(self.after_targets) if self.after_targets else "network.target"
        command = " ".join(self.command)

        return f"""[Unit]
Description={self.description}
After={after}

[Service]
Type=oneshot
ExecStart={command}
User={self.user}
Environment=PYENV_ROOT={os.environ.get("PYENV_ROOT", "")}
Environment=PATH={os.environ.get("PATH")}

[Install]
WantedBy=multi-user.target
"""

    def generate_timer_file(self) -> str:
        """Generate the content for the systemd timer file."""
        return f"""[Unit]
Description=Timer for {self.description}

[Timer]
OnBootSec={self.boot_delay}
OnUnitActiveSec={self.schedule}

[Install]
WantedBy=timers.target
"""

    def get_summary(self) -> str:
        """Get a one-line summary of the service."""
        return f"{self.description} (runs every {self.schedule})"


@dataclass
class ServiceConfigBase:
    """Base class for service configurations."""

    def get_services(self) -> list[SystemdServiceTemplate]:
        """Get list of all registered services."""
        return [
            getattr(self, name)
            for name, value in vars(self.__class__).items()
            if isinstance(value, field)
            and value.default is not None
            and isinstance(value.default, SystemdServiceTemplate)
        ]

    def __iter__(self):
        """Make service configs iterable."""
        return iter(self.get_services())


def service_configs(*services: SystemdServiceTemplate) -> Callable[[type[T]], type[T]]:
    """Decorator to create service configuration fields from templates.

    Args:
        *services: Service templates to register

    Returns:
        Decorated class with magical service handling capabilities
    """

    def wrapper(cls: type[T]) -> type[T]:
        # Make the class inherit from our base
        cls.__bases__ = (ServiceConfigBase,)

        # Add the services as class-level type hints
        annotations = getattr(cls, "__annotations__", {})
        for service in services:
            annotations[service.name] = SystemdServiceTemplate
        cls.__annotations__ = annotations

        # Create the fields using default_factory
        for service in services:
            # Create a factory function that returns this specific service
            def factory(s: SystemdServiceTemplate = service) -> SystemdServiceTemplate:
                return s

            setattr(cls, service.name, field(default_factory=factory, init=False))

        # Make it a dataclass
        return dataclass(cls)

    return wrapper
