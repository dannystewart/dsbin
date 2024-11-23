from __future__ import annotations

import subprocess
from pathlib import Path

from .systemd.service_list import ServiceConfigs
from .systemd.service_template import SystemdServiceTemplate

from dsutil.text import color, print_colored

# Define column widths
COLUMN_BUFFER = 2
SCRIPT_WIDTH = 16
DESC_WIDTH = 50


class SystemdManager:
    """Manages systemd service and timer creation and management."""

    def __init__(self):
        self.systemd_path = Path("/etc/systemd/system")

    def install_service(self, config: SystemdServiceTemplate) -> bool:
        """Install and enable a systemd service and timer. Returns success status."""
        if not self.systemd_path.exists():
            msg = "systemd directory not found."
            raise RuntimeError(msg)

        service_path = self.systemd_path / f"{config.name}.service"
        timer_path = self.systemd_path / f"{config.name}.timer"

        try:
            # Write service file
            service_path.write_text(config.generate_service_file())
            timer_path.write_text(config.generate_timer_file())

            # Set permissions
            service_path.chmod(0o644)
            timer_path.chmod(0o644)

            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], check=True)

            # Enable and start timer
            subprocess.run(["systemctl", "enable", f"{config.name}.timer"], check=True)
            subprocess.run(["systemctl", "start", f"{config.name}.timer"], check=True)

            return True

        except Exception as e:
            print(f"Failed to install service: {e}")
            # Clean up any partially created files
            if service_path.exists():
                service_path.unlink()
            if timer_path.exists():
                timer_path.unlink()
            return False

    def remove_service(self, name: str) -> bool:
        """Remove a systemd service and timer. Returns success status."""
        try:
            # Stop and disable timer
            subprocess.run(["systemctl", "stop", f"{name}.timer"], check=True)
            subprocess.run(["systemctl", "disable", f"{name}.timer"], check=True)

            # Remove files
            service_path = self.systemd_path / f"{name}.service"
            timer_path = self.systemd_path / f"{name}.timer"

            if service_path.exists():
                service_path.unlink()
            if timer_path.exists():
                timer_path.unlink()

            # Reload systemd
            subprocess.run(["systemctl", "daemon-reload"], check=True)

            return True

        except Exception as e:
            print(f"Failed to remove service: {e}")
            return False


def list_services(search_term: str = "") -> None:
    """List all available services with their descriptions."""
    configs = ServiceConfigs()

    services = [
        (name, config.get_summary())
        for name, config in vars(configs).items()
        if isinstance(config, SystemdServiceTemplate)
    ]

    if search_term:
        services = [
            (name, desc)
            for name, desc in services
            if search_term.lower() in name.lower() or search_term.lower() in desc.lower()
        ]

    if not services:
        print_colored(
            f"No services found{f' matching \'{search_term}\'' if search_term else ''}.", "yellow"
        )
        return

    service_width = max(len(name) for name, _ in services) + COLUMN_BUFFER

    print()
    print_colored(
        f"{"Service Name":<{service_width}} {"Description":<{DESC_WIDTH}}",
        "cyan",
        attrs=["bold", "underline"],
    )

    for name, desc in sorted(services):
        print(color(f"{name:<{service_width}} ", "green") + color(desc, "white"))
    print()
