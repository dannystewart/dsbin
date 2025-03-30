"""Version management tool for Python projects."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from dsbase import ArgParser
from dsbase.util import dsbase_setup

from dsbin.pybumper.beta.bump_type import BumpType
from dsbin.pybumper.beta.monorepo_helper import MonorepoHelper
from dsbin.pybumper.beta.pybumper import PyBumper

if TYPE_CHECKING:
    import argparse

dsbase_setup()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(description=__doc__, lines=1, arg_width=34)
    parser.add_argument(
        "type",
        nargs="*",
        default=[BumpType.PATCH],
        help="major, minor, patch, dev, alpha, beta, rc, post; or x.y.z",
    )
    parser.add_argument("-f", "--force", action="store_true", help="skip confirmation prompt")
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
        "--no-increment",
        action="store_true",
        help="do NOT increment version; just commit, tag, and push",
    )
    push_group.add_argument(
        "--no-push",
        action="store_true",
        help="increment version, commit, and tag - but do NOT push",
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
        PyBumper(args, package_name).perform_bump()
    finally:  # Change back to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    main()
