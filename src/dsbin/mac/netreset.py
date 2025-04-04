#!/usr/bin/env python3

"""macOS network reset script."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any

from polykit import polykit_setup
from polykit.cli import confirm_action
from polykit.parsers import print_color as colored
from polykit.shell import acquire_sudo

polykit_setup()

IP_TO_PING = "9.9.9.9"


def get_troubleshooting_steps(wifi_interface: str) -> list[dict[str, Any]]:
    """Get troubleshooting steps.

    Args:
        wifi_interface: Wi-Fi interface.

    Returns:
        List of troubleshooting steps.
    """
    return [
        {
            "action": "renewing the DHCP lease",
            "command": ["sudo", "ipconfig", "set", wifi_interface, "DHCP"],
        },
        {
            "action": "toggling Wi-Fi",
            "command": ["networksetup", "-setairportpower", wifi_interface, "off"],
            "toggle_wifi_on": True,
        },
        {
            "action": "flushing the DNS cache",
            "command": [
                ["sudo", "dscacheutil", "-flushcache"],
                ["sudo", "killall", "-HUP", "mDNSResponder"],
            ],
        },
        {
            "action": "removing temporary network files",
            "command": [
                [
                    "sudo",
                    "rm",
                    "-f",
                    "/Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist",
                ],
                [
                    "sudo",
                    "rm",
                    "-f",
                    "/Library/Preferences/SystemConfiguration/NetworkInterfaces.plist",
                ],
                ["sudo", "rm", "-f", "/Library/Preferences/SystemConfiguration/preferences.plist"],
            ],
        },
    ]


def check_connection() -> bool:
    """Check if internet connection is available."""
    try:
        subprocess.check_call(
            ["ping", "-c", "1", IP_TO_PING], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def identify_wifi_interface() -> str:
    """Identify the Wi-Fi interface."""
    return subprocess.getoutput(
        "networksetup -listallhardwareports | awk '/Wi-Fi/{getline; print $2}'"
    )


def main() -> None:
    """Main function."""
    wifi_interface = identify_wifi_interface()
    troubleshooting_steps = get_troubleshooting_steps(wifi_interface)

    for step in troubleshooting_steps:
        if confirm_action(f"Do you want to proceed with {step['action']}?"):
            if step["action"] == "renewing the DHCP lease" and not acquire_sudo():
                print(colored("sudo access is required for this action. Aborting.", "red"))
                sys.exit(1)

            if isinstance(step["command"][0], list):
                for cmd in step["command"]:
                    subprocess.run(cmd, check=False)
            else:
                subprocess.run(step["command"], check=False)

            if step.get("toggle_wifi_on"):
                time.sleep(2)
                subprocess.run(
                    ["networksetup", "-setairportpower", wifi_interface, "on"], check=False
                )

            if check_connection():
                print(colored("Internet is working fine.", "green"))
                sys.exit(0)

    print(colored("Completed all steps but still having issues.", "red"))


if __name__ == "__main__":
    if os.uname().sysname != "Darwin":  # type: ignore
        print(colored("This script is intended only for macOS. Aborting.", "red"))
        sys.exit(1)

    if check_connection():
        print("Internet is working fine.")
        sys.exit(0)

    main()
