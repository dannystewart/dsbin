#!/usr/bin/env python3
"""Show installed versions of DS packages."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from importlib import metadata

from packaging import version

from dsutil.text import color


@dataclass
class PackageVersions:
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

        # Get all version tags and clean them up
        versions = []
        for ref in result.stdout.splitlines():
            tag = ref.split("/")[-1]
            if tag.startswith("v"):
                # Clean up Git ref notation and parse version
                clean_tag = tag.split("^")[0].lstrip("v")
                try:
                    versions.append(version.parse(clean_tag))
                except version.InvalidVersion:
                    continue

        # Sort with packaging.version comparison
        if versions:
            return str(max(versions))
        return None

    except subprocess.CalledProcessError:
        return None


def get_package_info(package: str, check_latest: bool = False) -> PackageVersions:
    """Get package version information."""
    try:
        current = metadata.version(package)
    except metadata.PackageNotFoundError:
        current = None

    latest = get_latest_version(package) if check_latest else None
    return PackageVersions(package, current, latest)


def format_version_info(versions: PackageVersions) -> tuple[str, str]:
    """Format package status and version display."""
    current_version = color(f"{versions.current}", "green")
    latest_version = color(f"{versions.latest}", "yellow")

    if not versions.current:
        symbol = color("✗", "red", attrs=["bold"])
        ver = color("Not installed", "red")
        if versions.latest:
            ver = f"{ver}\n     Latest version: {latest_version}"
        return symbol, ver

    if versions.latest and version.parse(versions.latest) > version.parse(versions.current):
        symbol = color("⚠", "yellow", attrs=["bold"])
        ver = f"{current_version} ({latest_version} available)"
        return symbol, ver

    symbol = color("✓", "green", attrs=["bold"])
    return symbol, current_version


def main() -> None:
    """Show versions of DS packages."""
    packages = ["dsbin", "dsutil"]
    any_updates = False

    for package in packages:
        versions = get_package_info(package, check_latest=True)
        name = color(f"{package}:", "cyan", attrs=["bold"])
        symbol, version = format_version_info(versions)

        print(f"{symbol} {name} {version}")
        any_updates = any_updates or (
            versions.latest and (not versions.current or versions.latest > versions.current)
        )


if __name__ == "__main__":
    main()
