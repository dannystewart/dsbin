from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from polykit.cli import is_root_user
from polykit.formatters import color, print_color

from dsbin.systemd.service_list import ServiceConfigs
from dsbin.systemd.systemd import SystemdServiceTemplate

# Define column widths
COLUMN_BUFFER = 2
SCRIPT_WIDTH = 16
DESC_WIDTH = 50


class SystemdManager:
    """Manages systemd service and timer creation and management."""

    def __init__(self):
        self.systemd_path = Path("/etc/systemd/system")

    def install_service(self, config: SystemdServiceTemplate) -> bool:
        """Install and enable a systemd service and timer. Returns success status.

        Raises:
            RuntimeError: If the systemd directory is not found.
        """
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
        print_color(
            f"No services found{f" matching '{search_term}'" if search_term else ''}.", "yellow"
        )
        return

    service_width = max(len(name) for name, _ in services) + COLUMN_BUFFER

    print()
    print_color(
        f"{'Service Name':<{service_width}} {'Description':<{DESC_WIDTH}}",
        "cyan",
        style=["bold", "underline"],
    )

    for name, desc in sorted(services):
        print(color(f"{name:<{service_width}} ", "green") + color(desc, "white"))
    print()


def handle_services(args: argparse.Namespace) -> int:
    """Get available services and perform requested actions.

    Raises:
        ValueError: If an unknown command is provided.
    """
    manager = SystemdManager()
    configs = ServiceConfigs()

    # Get the service config if it exists
    service_config = None
    for name, config in vars(configs).items():
        if isinstance(config, SystemdServiceTemplate) and name == args.service:
            service_config = config
            break

    if not service_config:
        print_color(f"Service '{args.service}' not found.", "red")
        return 1

    if args.command == "install":
        if manager.install_service(service_config):
            print_color(f"Successfully installed {args.service} service.", "green")
            return 0
        return 1

    if args.command == "remove":
        if manager.remove_service(args.service):
            print_color(f"Successfully removed {args.service} service.", "green")
            return 0
        return 1
    msg = "Unknown command."
    raise ValueError(msg)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Manage systemd services for DS utilities")
    parser.add_argument("command", choices=["install", "remove", "list"], help="Action to perform")
    parser.add_argument("service", nargs="?", help="Service to act on")
    parser.add_argument("--search", help="Search term when listing services", default="")
    return parser.parse_args()


def main() -> int:
    """Main function for managing systemd services."""
    if not is_root_user():
        print_color("This script must be run as root.", "red")
        return 1

    args = parse_args()

    if args.command == "list":
        list_services(args.search)
        return 0

    if not args.service:
        print_color(f"Service name required for {args.command} command.", "red")
        return 1

    return handle_services(args)


if __name__ == "__main__":
    sys.exit(main())
