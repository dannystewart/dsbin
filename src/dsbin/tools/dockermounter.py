#!/usr/bin/env python3

"""Checks to see if mount points are mounted, and act accordingly."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import termios
import tty

from termcolor import colored
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dsutil.text import ColorName

logging.basicConfig(
    filename="mount_check.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

mount_points = [
    "/mnt/Danny",
    "/mnt/Downloads",
    "/mnt/Media",
    "/mnt/Music",
    "/mnt/Storage",
]

containers = [
    "sonarr",
    "radarr",
    "lidarr",
    "readarr",
    "bazarr",
    "prowlarr",
    "whisparr",
    "deluge",
    "sabnzbd",
    "tautulli",
    "ombi",
    "audiobookshelf",
]


def get_single_char_input(prompt: str) -> str:
    """Reads a single character without requiring the Enter key. Mainly for confirmation prompts."""
    print(prompt, end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return char


def confirm_action(
    prompt: str, default_to_yes: bool = False, prompt_color: ColorName = "white"
) -> bool:
    """Asks the user to confirm an action."""
    options = "[Y/n]" if default_to_yes else "[y/N]"
    full_prompt = colored(f"{prompt} {options} ", prompt_color)
    sys.stdout.write(full_prompt)

    char = get_single_char_input("").lower()

    sys.stdout.write(char + "\n")
    sys.stdout.flush()

    return char != "n" if default_to_yes else char == "y"


def run_subprocess(command: str) -> str:
    """Run a subprocess command and handle errors."""
    try:
        logging.info("Running command: %s", " ".join(command))
        output = subprocess.run(command, check=True, capture_output=True)
        return output.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        logging.error("Command '%s' failed with: %s", e.cmd, e.stderr.decode().strip())
        raise


def is_mounted(path: str) -> bool:
    """Check to see if the folder is mounted."""
    return os.path.ismount(path)


def list_directory_contents(mount_point: str) -> bool:
    """List contents of the directory."""
    if os.path.exists(mount_point):
        if contents := os.listdir(mount_point):
            print("Directory is not empty. Contents:")
            for item in contents:
                print(item)
            return True
        print("Directory is empty.")
        return False
    print("Directory does not exist.")
    return False


def clear_mount_point(mount_point: str) -> None:
    """Clear the mount point."""
    non_empty = list_directory_contents(mount_point)
    if non_empty and confirm_action(
        f"Are you sure you want to remove all contents in {mount_point}?"
    ):
        run_subprocess(["rm", "-rf", f"{mount_point}/*"])
    else:
        logging.info("User aborted clearing mount point at %s.", mount_point)


def remount(mount_point: str) -> None:
    """Remount the mount point."""
    subprocess.run(["mount", mount_point], check=True)


def restart_docker_containers() -> None:
    """Restart Docker containers."""
    for container in containers:
        subprocess.run(["docker", "restart", container], check=True)


def main() -> None:
    """Main function."""
    anything_unmounted = False
    for mount_point in mount_points:
        if not is_mounted(mount_point):
            logging.warning("Mount point %s is not mounted.", mount_point)
            print(colored(f"Mount point {mount_point} is not mounted.", "yellow"))
            anything_unmounted = True
            try:
                clear_mount_point(mount_point)
                remount(mount_point)
            except subprocess.CalledProcessError as e:
                print(colored(f"An error occurred: {e}", "red"))
                logging.error("Error while handling unmounted path %s: %s", mount_point, e)

    if anything_unmounted:
        print(colored("Restarting Docker containers...", "green"))
        logging.info("Restarting Docker containers due to unmounted paths.")
        restart_docker_containers()

    if not anything_unmounted:
        print(colored("All mount points are mounted. No action required.", "green"))
        logging.info("All mount points were mounted. No action required.")


if __name__ == "__main__":
    main()
