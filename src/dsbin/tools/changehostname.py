#!/usr/bin/env python3

"""Changes the system hostname in all the relevant places."""

from __future__ import annotations

import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

from polykit.cli import confirm_action, is_root_user
from polykit.formatters import print_color


def run_hostname_command(new_hostname: str) -> None:
    """Run the hostname command."""
    if shutil.which("hostnamectl"):
        subprocess.run(["hostnamectl", "set-hostname", new_hostname], check=True)

    subprocess.run(["hostname", new_hostname], check=True)


def get_current_hostname() -> str:
    """Get the current hostname."""
    old_hostname = socket.gethostname()

    print(f"Current hostname: {old_hostname}")
    print("Hostname command output: " + subprocess.check_output(["hostname"]).decode().strip())

    if Path("/etc/hostname").exists():
        print(
            "Contents of /etc/hostname: "
            + Path("/etc/hostname").read_text(encoding="utf-8").strip()
        )

    return old_hostname


def update_hostname_file(new_hostname: str) -> None:
    """Update the /etc/hostname file."""
    if Path("/etc/hostname").exists():
        Path("/etc/hostname").write_text(new_hostname + "\n", encoding="utf-8")


def update_hosts_file(old_hostname: str, new_hostname: str) -> None:
    """Update the /etc/hosts file."""
    with Path("/etc/hosts").open(mode="r+", encoding="utf-8") as hosts_file:
        content = hosts_file.read()
        content = content.replace(old_hostname, new_hostname)
        hosts_file.seek(0)
        hosts_file.write(content)
        hosts_file.truncate()


def validate_hostname(old_hostname: str, new_hostname: str) -> bool:
    """Ensure that the new hostname is valid.

    The hostname must be between 1 and 253 characters, must not contain any invalid characters, and
    must not start or end with a hyphen. It must also be different from the current hostname.

    Args:
        old_hostname: The current hostname.
        new_hostname: The new hostname.

    Returns:
        True if the hostname is valid, False otherwise.
    """
    if new_hostname == old_hostname:
        print_color("The new hostname is the same as the current hostname. Exiting.", "red")
        return False

    if not 1 <= len(new_hostname) <= 253:
        print_color("Hostname must be between 1 and 253 characters long.", "red")
        return False

    if not re.match(r"^(?!-)[A-Za-z0-9-]+(?<!-)$", new_hostname):
        print_color("Hostname contains invalid characters or starts/ends with a hyphen.", "red")
        return False

    return True


def main() -> None:
    """Main function."""
    old_hostname = get_current_hostname()

    if not is_root_user():
        print_color("\nPlease run with root privileges to modify hostname.", "red")
        sys.exit(1)

    new_hostname = input("\nEnter new hostname: ")

    if not new_hostname:
        print_color("No hostname provided. Exiting.", "red")
        sys.exit(1)

    if not confirm_action(f"Proceed with changing hostname to {new_hostname}?"):
        print_color("Exiting.", "red")
        sys.exit(0)

    run_hostname_command(new_hostname)
    update_hostname_file(new_hostname)
    update_hosts_file(old_hostname, new_hostname)

    print_color("Please reboot to finalize changes.", "yellow")


if __name__ == "__main__":
    main()
