from __future__ import annotations

import stat
from pathlib import Path

WRAPPER_SCRIPT = """#!/bin/bash

# Create a named pipe
PIPE=/tmp/update_sudo_pipe
mkfifo $PIPE

# Cleanup function
cleanup() {
    rm -f $PIPE
    exit
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Function to check if sudo is needed
needs_sudo() {
    dsupdater --check-sudo
    return $?
}

# Function to refresh sudo timestamp
refresh_sudo() {
    sudo -v
}

# Check if sudo is needed
if needs_sudo; then
    if sudo -n true 2>/dev/null; then
        refresh_sudo
        echo "sudo_available" > $PIPE &
    else
        if refresh_sudo; then
            echo "sudo_available" > $PIPE &
        else
            echo "sudo_unavailable" > $PIPE &
        fi
    fi
else
    echo "sudo_not_needed" > $PIPE &
fi

# Run the updater script
dsupdater "$@"
"""


def install_wrapper() -> None:
    """Install the wrapper script to the user's bin directory."""
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    wrapper_path = bin_dir / "updater"
    wrapper_path.write_text(WRAPPER_SCRIPT)

    # Make executable
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)

    print(f"Installed wrapper script to {wrapper_path}")


def main() -> None:
    """Entry point for installer."""
    install_wrapper()
