#!/usr/bin/env python3

"""Check all interdependencies between dsbin and dsbin."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from typing import TYPE_CHECKING

from polykit.cli import ArgParser
from polykit.core import polykit_setup
from polykit.formatters import color
from polykit.log import Logician

if TYPE_CHECKING:
    import argparse

polykit_setup()
logger = Logician.get_logger(simple=True)

DEFAULT_PACKAGES: list[str] = [
    "arguer",
    "dsbin",
    "enviromancer",
    "logician",
    "masterclass",
    "pathkeeper",
    "polykit.shell",
    "parseutil",
    "walking_man",
]


def check_imports(package_name: str) -> bool:
    """Check all imports in a package recursively.

    Args:
        package_name: Name of the package to check.

    Returns:
        True if all imports succeed, False otherwise.
    """
    try:
        package = importlib.import_module(package_name)
        logger.debug("Successfully imported %s.", package_name)
    except ImportError as e:
        logger.error("Could not import %s: %s", package_name, str(e))
        return False

    all_modules = []
    failed_modules = []

    # Walk through all submodules
    for _, name, _ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            importlib.import_module(name)
            all_modules.append(name)
        except ImportError as e:
            logger.error("Could not import %s: %s", name, str(e))
            failed_modules.append((name, str(e)))

    if failed_modules:
        logger.error("Failed to import %s modules in %s.", len(failed_modules), package_name)
        for module, error in failed_modules:
            print(f"  - {color(module, 'red')}: {error}")
        return False

    logger.debug("Successfully imported all %s modules in %s.", len(all_modules), package_name)
    return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = ArgParser(description="Check package dependencies")
    parser.add_argument(
        "--packages",
        nargs="+",
        default=DEFAULT_PACKAGES,
        help="packages to check (defaults to all)",
    )
    return parser.parse_args()


def main() -> int:
    """Check all interdependencies between packages.

    Returns:
        0 if all checks pass, 1 otherwise.
    """
    args = parse_args()
    packages = args.packages or DEFAULT_PACKAGES
    success = True

    for pkg in packages:
        if not check_imports(pkg):
            success = False

    if success:
        logger.info("All dependency checks passed! 🎉")
    else:
        logger.error("Some dependency checks failed. ☹️")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
