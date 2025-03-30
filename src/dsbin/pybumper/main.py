"""Version management tool for Python projects."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dsbase.util import dsbase_setup

from dsbin.pybumper.bump_type import BumpType
from dsbin.pybumper.monorepo_helper import MonorepoHelper
from dsbin.pybumper.version_bumper import VersionBumper

dsbase_setup()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "type",
        nargs="*",
        default=[BumpType.PATCH],
        help="version bump type(s): major, minor, patch, dev, alpha, beta, rc, post, or x.y.z",
    )
    parser.add_argument(
        "-p",
        "--package",
        help="package name to bump (e.g., dsbase, dsbin). Auto-detected if not provided.",
    )
    parser.add_argument("-f", "--force", action="store_true", help="skip confirmation prompt")
    parser.add_argument(
        "-m", "--message", help="custom commit message (default: 'Bump version to x.y.z')"
    )

    # Mutually exclusive group for push options
    push_group = parser.add_mutually_exclusive_group()
    push_group.add_argument(
        "--keep-version",
        action="store_true",
        help="tag and push the current version without incrementing",
    )
    push_group.add_argument(
        "--no-push",
        action="store_true",
        help="commit and tag changes but don't push to remote",
    )

    return parser.parse_args()


def main() -> None:
    """Perform version bump."""
    args = parse_args()

    # Detect package and paths
    package_name, package_path = MonorepoHelper.detect_package(args.package)

    # Save the original directory and change to the package directory
    original_dir = Path.cwd()
    os.chdir(package_path)

    try:  # Pass package name to VersionBumper
        VersionBumper(args, package_name).perform_bump()
    finally:  # Change back to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    main()
