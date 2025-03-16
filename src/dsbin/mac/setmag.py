#!/usr/bin/env python3

"""Set MagSafe light according to power status."""

from __future__ import annotations

import os
import subprocess
import sys

from dsbase import configure_traceback

configure_traceback()


def log_message(message: str) -> None:
    """Log a message to stdout or syslog."""
    if sys.stdout.isatty():
        print(message)
    else:
        subprocess.run(["logger", "-p", "user.info", message], check=False)


if os.uname().sysname != "Darwin":  # type: ignore
    log_message("This can only be run on macOS. Aborting.")
    sys.exit(1)

output = subprocess.getoutput("pmset -g batt")

if "Now drawing from 'AC Power'" in output and "AC attached; not charging" in output:
    log_message("Connected to power but not charging, so setting MagSafe to green")
    subprocess.run(
        ["/usr/local/bin/gtimeout", "3s", "sudo", "/usr/local/bin/smc", "-k", "ACLC", "-w", "03"],
        check=False,
    )
elif "Now drawing from 'AC Power'" in output:
    log_message("Connected to power and charging, resetting MagSafe to default behavior")
    subprocess.run(
        ["/usr/local/bin/gtimeout", "3s", "sudo", "/usr/local/bin/smc", "-k", "ACLC", "-w", "00"],
        check=False,
    )
else:
    log_message("Unable to determine status, resetting MagSafe to default behavior")
    subprocess.run(
        ["/usr/local/bin/gtimeout", "3s", "sudo", "/usr/local/bin/smc", "-k", "ACLC", "-w", "00"],
        check=False,
    )
