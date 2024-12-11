#!/usr/bin/env python3
"""Show installed versions of DS packages."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata

from dsutil.text import color


@dataclass
class PackageInfo:
    """Package version information."""

    name: str
    current: str | None
    latest: str | None


def get_latest_version(package: str) -> str | None:
    """Get latest version from GitLab."""
    gitlab_base = "https://gitlab.dannystewart.com/danny"
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--tags", f"{gitlab_base}/{package}.git"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Get all version tags, sort them, take the last one
        tags = [
            ref.split("/")[-1]
            for ref in result.stdout.splitlines()
            if ref.split("/")[-1].startswith("v")
            and not any(x in ref for x in ("dev", "a", "b", "rc"))  # Ignore pre-releases
        ]
        return tags[-1].lstrip("v") if tags else None
    except subprocess.CalledProcessError:
        return None


def get_package_info(package: str, check_latest: bool = False) -> PackageInfo:
    """Get package version information."""
    try:
        current = metadata.version(package)
    except metadata.PackageNotFoundError:
        current = None

    latest = get_latest_version(package) if check_latest else None
    return PackageInfo(package, current, latest)


def update_package(package: str) -> bool:
    """Update package from GitLab."""
    gitlab_base = "https://gitlab.dannystewart.com/danny"
    try:
        subprocess.run(
            ["pip", "install", "-U", f"git+{gitlab_base}/{package}.git"],
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def format_status(info: PackageInfo) -> tuple[str, str]:
    """Format package status and version display."""
    current_version = color(f"{info.current}", "green")
    latest_version = color(f"{info.latest}", "yellow")

    if not info.current:
        symbol = color("✗", "red", attrs=["bold"])
        version = color("Not installed", "red")
        if info.latest:
            version = f"{version}\n     Latest version: {latest_version}"
        return symbol, version

    if info.latest and info.latest > info.current:
        symbol = color("⚠", "yellow", attrs=["bold"])
        version = f"{current_version} ({latest_version} available)"
        return symbol, version

    symbol = color("✓", "green", attrs=["bold"])
    return symbol, current_version


def main() -> None:
    """Show versions of DS packages."""
    parser = argparse.ArgumentParser(description="Show DS package versions")
    parser.add_argument(
        "--update",
        action="store_true",
        help="update packages to latest version",
    )
    args = parser.parse_args()

    packages = ["dsbin", "dsutil"]
    any_updates = False

    for package in packages:
        info = get_package_info(package, check_latest=True)
        name = color(f"{package}:", "cyan", attrs=["bold"])
        symbol, version = format_status(info)

        print(f"{symbol} {name} {version}")
        any_updates = any_updates or (
            info.latest and (not info.current or info.latest > info.current)
        )

    if args.update and any_updates:
        print(f"\n{format_status('Updating packages...', 'info')}")
        for package in packages:
            info = get_package_info(package, check_latest=True)
            if info.latest and (not info.current or info.latest > info.current):
                print(f"\n{format_status(f'Updating {package}...', 'info')}")
                if update_package(package):
                    print(format_status(f"{package} updated successfully", "success"))
                else:
                    print(format_status(f"Failed to update {package}", "error"))
                    sys.exit(1)


if __name__ == "__main__":
    main()
