#!/usr/bin/env python3

"""Wrapper for the macOS Installer command-line utility."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from logician import Logician
from polykit import polykit_setup
from polykit.cli import confirm_action
from polykit.parsers import color

from dsbin.files import FileManager

polykit_setup()

logger = Logician.get_logger()


def install_pkg(
    pkg_paths: Path | list[Path],
    target: str = "/",
    from_dmg: bool = False,
    dmg_path: Path | None = None,
    mount_point: str | None = None,
) -> bool:
    """Install a .pkg file or list of .pkg files on macOS using the installer command-line utility.

    Args:
        pkg_paths: Path to the .pkg file or list of paths to .pkg files to install.
        target: The target volume of the installation. Default is the root volume.
        from_dmg: Indicates if the .pkg file is being installed from a DMG. Default is False.
        dmg_path: Path to the .dmg file if the .pkg is being installed from a DMG.
        mount_point: Mount point of the .dmg file if applicable.

    Returns:
        True if all installations were successful, False otherwise.
    """
    files = FileManager()
    if isinstance(pkg_paths, Path):
        pkg_paths = [pkg_paths]

    success = True
    for pkg_path in pkg_paths:
        if not Path(pkg_path).is_file():
            logger.error("Error: File '%s' does not exist.", pkg_path)
            success = False
            continue

        install_command = ["sudo", "installer", "-pkg", pkg_path, "-target", target]

        try:
            subprocess.run(install_command, check=True)
            logger.info("Successfully installed %s", pkg_path)
            if from_dmg and dmg_path and mount_point:
                if confirm_action(color(f"Unmount and delete {dmg_path}?", "yellow")):
                    unmount_dmg(mount_point)
                    files.delete(dmg_path)
            elif not from_dmg and confirm_action(color(f"Delete {pkg_path}?", "yellow")):
                files.delete(pkg_path)
        except subprocess.CalledProcessError as e:
            logger.error("Error during installation: %s", str(e))
            success = False

    return success


def install_pkg_from_dmg(dmg_path: Path, pkg_name: str | None = None, target: str = "/") -> None:
    """Mount a DMG file, installs the specified PKG file from inside it, and then unmount the DMG.
    If no PKG name is specified, install the first PKG file found within the DMG.

    Args:
        dmg_path: Path to the .dmg file.
        pkg_name: Name of the .pkg file to install in the .dmg. If None, installs the first found.
        target: The target volume of the installation. Default is the root volume.
    """
    mount_point = mount_dmg(dmg_path)
    if not mount_point:
        return

    try:
        if pkg_path := find_pkg_in_dmg(mount_point, pkg_name):
            install_pkg(pkg_path, target, from_dmg=True, dmg_path=dmg_path, mount_point=mount_point)
        else:
            logger.error("No .pkg file found in %s", dmg_path)
    finally:
        if mount_point and os.path.ismount(mount_point):
            unmount_dmg(mount_point)


def find_pkg_in_dmg(mount_point: str, pkg_name: str | None = None) -> Path | None:
    """Find specified PKG file in the mounted DMG, or the first PKG file if no name is provided.

    Args:
        mount_point: The mount point of the DMG.
        pkg_name: The name of the PKG file to find. If None, find the first PKG file.

    Returns:
        The path to the PKG file if found, otherwise None.
    """
    if pkg_name:
        pkg_path = Path(mount_point) / pkg_name
        if Path(pkg_path).is_file():
            return pkg_path
        logger.error("Error: File '%s' does not exist.", pkg_path)
        return None
    for root, _, files in os.walk(mount_point):
        for file in files:
            if file.endswith(".pkg"):
                return Path(root) / file
    return None


def mount_dmg(dmg_path: Path) -> str | None:
    """Mount a DMG file and return the mount point.

    Args:
        dmg_path: Path to the .dmg file to mount.

    Returns:
        The mount point path, or None if there was an error.
    """
    try:
        hdiutil_output = subprocess.check_output([
            "hdiutil",
            "attach",
            dmg_path,
            "-nobrowse",
            "-noverify",
        ])
        if mount_point := next(
            (
                line.split(b"\t")[-1].decode("utf-8")
                for line in hdiutil_output.splitlines()
                if b"/Volumes" in line
            ),
            None,
        ):
            logger.info("Mounted %s at %s", dmg_path, mount_point)
            return mount_point
        logger.error("Could not determine mount point for %s", dmg_path)
        return None
    except subprocess.CalledProcessError as e:
        logger.error("Error mounting dmg: %s", str(e))
        return None


def unmount_dmg(mount_point: str) -> None:
    """Unmount a DMG file.

    Args:
        mount_point: Mount point to unmount.
    """
    try:
        subprocess.run(["hdiutil", "detach", mount_point], check=True)
        logger.info("Unmounted %s", mount_point)
    except subprocess.CalledProcessError as e:
        logger.error("Error unmounting %s: %s", mount_point, str(e))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    paths_str = "Path(s) to .pkg/.dmg file(s) to install. Supports wildcards like *.pkg."
    target_str = "The target volume of the installation. Default is the root volume."
    dmg_pkg_str = (
        "Name of the .pkg file within the .dmg. If not provided, installs the first .pkg found."
    )

    parser = argparse.ArgumentParser(
        description="Wrapper for macOS Installer command-line utility."
    )
    parser.add_argument("paths", type=str, nargs="+", help=paths_str)
    parser.add_argument("-t", "--target", type=str, default="/", help=target_str)
    parser.add_argument("--dmg-pkg-name", type=str, default=None, help=dmg_pkg_str)

    return parser.parse_args()


def main() -> None:
    """Install a PKG file using the macOS install utility."""
    args = parse_args()

    for path_str in args.paths:
        path = Path(path_str)
        if "*" in path_str or "?" in path_str:
            pkg_list = list(Path().glob(path_str))
            install_pkg(pkg_list, args.target)
        elif path.suffix == ".dmg":
            install_pkg_from_dmg(path, args.dmg_pkg_name, args.target)
        elif path.suffix == ".pkg":
            install_pkg(path, args.target)
        else:
            logger.error("Unsupported file type: %s", path)


if __name__ == "__main__":
    main()
