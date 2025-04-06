#!/usr/bin/env python3

"""Show installed versions of my packages and flag deprecated packages."""

from __future__ import annotations

from typing import Any

from packaging import version
from polykit.cli import walking_man
from polykit.formatters import color
from polykit.packages import PackageSource, VersionChecker, VersionInfo

PACKAGES: list[dict[str, Any]] = [
    {"name": "dsbin", "source": PackageSource.PYPI},
    {"name": "polykit", "source": PackageSource.PYPI},
]

# Packages that should no longer be installed
DEPRECATED_PACKAGES: list[dict[str, Any]] = [
    {"name": "arguer", "source": PackageSource.PYPI},
    {"name": "devpkg", "source": PackageSource.PYPI},
    {"name": "ds-iplookup", "source": PackageSource.PYPI},
    {"name": "dsbase", "source": PackageSource.PYPI},
    {"name": "dsconfig", "source": PackageSource.PYPI},
    {"name": "dsmetapackage", "source": PackageSource.PYPI},
    {"name": "dsupdater", "source": PackageSource.PYPI},
    {"name": "dsutil", "source": PackageSource.PYPI},
    {"name": "enviromancer", "source": PackageSource.PYPI},
    {"name": "logician", "source": PackageSource.PYPI},
    {"name": "masterclass", "source": PackageSource.PYPI},
    {"name": "parseutil", "source": PackageSource.PYPI},
    {"name": "pathkeeper", "source": PackageSource.PYPI},
    {"name": "shelper", "source": PackageSource.PYPI},
    {"name": "textparse", "source": PackageSource.PYPI},
    {"name": "timecapsule", "source": PackageSource.PYPI},
    {"name": "walking-man", "source": PackageSource.PYPI},
]


def format_version_info(versions: VersionInfo) -> tuple[str, str]:
    """Format package status and version display."""
    current_version = color(f"{versions.current}", "green")
    latest_version = color(f"{versions.latest}", "yellow")

    if not versions.current:
        symbol = color("✗", "red", style=["bold"])
        ver = color("Not installed", "red")
        if versions.latest:
            ver = f"{ver}\n     Latest version: {latest_version}"
        return symbol, ver

    if versions.latest and version.parse(versions.latest) > version.parse(versions.current):
        symbol = color("⚠", "yellow", style=["bold"])
        ver = f"{current_version} ({latest_version} available)"
        return symbol, ver

    symbol = color("✓", "green", style=["bold"])
    return symbol, current_version


def format_deprecated_info(versions: VersionInfo) -> tuple[str | None, str | None]:
    """Format deprecated package status and version display."""
    if not versions.current:
        # Not installed - this is good for deprecated packages
        return None, None

    # Package is installed but should be removed
    symbol = color("⚠", "red", style=["bold"])
    ver = color(f"{versions.current}", "red")
    ver = f"{ver} (deprecated - should be removed)"
    return symbol, ver


def main() -> None:
    """Show versions of my packages and flag deprecated packages."""
    checker = VersionChecker()
    any_updates = False

    print(color("Active Packages:", style=["bold"]))
    for pkg in PACKAGES:
        pkg_name = pkg.pop("name")
        source = pkg.pop("source")

        # Check version information
        info = checker.check_package(pkg_name, source=source, **pkg)

        # Format and display the information
        name = color(f"{pkg_name}:", "cyan", style=["bold"])
        symbol, version_str = format_version_info(info)

        print(f"{symbol} {name} {version_str}")
        any_updates = any_updates or info.update_available

    print()  # Blank line for spacing

    with walking_man(loading_text="Checking for deprecated packages...", speed=0.08):
        # Check for deprecated packages that are still installed
        deprecated_found = []
        for pkg in DEPRECATED_PACKAGES:
            pkg_name = pkg.pop("name")
            source = pkg.pop("source")

            # Check if the package is installed
            info = checker.check_package(pkg_name, source=source, **pkg)

            # Only process if the package is actually installed
            symbol, version_str = format_deprecated_info(info)
            if symbol and version_str:
                deprecated_found.append((pkg_name, symbol, version_str))

    # Display deprecated packages if any were found
    if deprecated_found:
        print(color("Deprecated Packages:", style=["bold"]))
        for pkg_name, symbol, version_str in deprecated_found:
            name = color(f"{pkg_name}:", "cyan", style=["bold"])
            print(f"{symbol} {name} {version_str}")
    else:
        print(color("✓ No deprecated packages found!", "green"))


if __name__ == "__main__":
    main()
