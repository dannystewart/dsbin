#!/usr/bin/env python3

"""Script to help with running Watchtower for Docker."""

from __future__ import annotations

import subprocess

import inquirer


def run_watchtower(run_once: bool, restart: bool, schedule: bool) -> None:
    """Run Watchtower for Docker.

    Args:
        run_once: Whether to run Watchtower once.
        restart: Whether to include restarting containers.
        schedule: The schedule on which to run Watchtower.
    """
    cmd = [
        "docker",
        "run",
        "--rm" if run_once else "-d",
        "--name",
        "watchtower",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        "containrrr/watchtower",
        "--cleanup",
    ]

    if run_once:
        cmd.append("--run-once")
    else:
        cmd.extend(["--restart", "always"])

    if restart:
        cmd.append("--include-restarting")

    if schedule:
        cmd.extend(["--schedule", str(schedule)])

    subprocess.run(cmd, check=False)


def main() -> None:
    """Present menu for Watchtower options.

    Raises:
        SystemExit: If the user exits the menu.
    """
    questions = [
        inquirer.List(
            "config",
            message="Choose configuration",
            choices=[
                ("Run Watchtower once, restart containers now", (True, True, None)),
                ("Run Watchtower once, do NOT restart containers", (True, False, None)),
                ("Run Watchtower always, restart containers now", (False, True, None)),
                ("Run Watchtower always, do NOT restart containers", (False, False, None)),
                (
                    "Run Watchtower daily at 4am, restart containers now",
                    (False, True, "0 0 4 * * *"),
                ),
                (
                    "Run Watchtower daily at 4am, do NOT restart containers",
                    (False, False, "0 0 4 * * *"),
                ),
            ],
        ),
    ]

    answer = inquirer.prompt(questions)
    if answer is None:
        raise SystemExit

    run_once, restart, schedule = answer["config"]

    run_watchtower(run_once, restart, schedule)


if __name__ == "__main__":
    main()
