#!/usr/bin/env python3

"""Set MagSafe light according to power status."""

from __future__ import annotations

import subprocess

from logician import Logician
from polykit import polykit_setup
from polykit.core import platform_check

polykit_setup()
platform_check("Darwin")

logger = Logician.get_logger("setmag")


def main() -> None:
    """Run the main script functionality."""
    output = subprocess.getoutput("pmset -g batt")

    if "Now drawing from 'AC Power'" in output and "AC attached; not charging" in output:
        logger.info("Connected to power but not charging, so setting MagSafe to green")
        subprocess.run(
            [
                "/usr/local/bin/gtimeout",
                "3s",
                "sudo",
                "/usr/local/bin/smc",
                "-k",
                "ACLC",
                "-w",
                "03",
            ],
            check=False,
        )
    elif "Now drawing from 'AC Power'" in output:
        logger.info("Connected to power and charging, resetting MagSafe to default behavior")
        subprocess.run(
            [
                "/usr/local/bin/gtimeout",
                "3s",
                "sudo",
                "/usr/local/bin/smc",
                "-k",
                "ACLC",
                "-w",
                "00",
            ],
            check=False,
        )
    else:
        logger.info("Unable to determine status, resetting MagSafe to default behavior")
        subprocess.run(
            [
                "/usr/local/bin/gtimeout",
                "3s",
                "sudo",
                "/usr/local/bin/smc",
                "-k",
                "ACLC",
                "-w",
                "00",
            ],
            check=False,
        )


if __name__ == "__main__":
    main()
