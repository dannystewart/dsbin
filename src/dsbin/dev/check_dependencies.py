#!/usr/bin/env python3
"""Check all interdependencies between dsbin and dsbase."""

from __future__ import annotations

import importlib
import pkgutil
import sys

from dsbase import LocalLogger
from dsbase.text import color, print_colored
from dsbase.util import dsbase_setup

dsbase_setup()
logger = LocalLogger().get_logger()


def check_imports(package_name: str) -> bool:
    """Check all imports in a package recursively.

    Args:
        package_name: Name of the package to check.

    Returns:
        True if all imports succeed, False otherwise.
    """
    try:
        package = importlib.import_module(package_name)
        print_colored(f"Successfully imported {package_name}", "green")
    except ImportError as e:
        print_colored(f"ERROR: Could not import {package_name}: {e}", "red")
        return False

    all_modules = []
    failed_modules = []

    # Walk through all submodules
    for _, name, _ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            importlib.import_module(name)
            all_modules.append(name)
        except ImportError as e:
            print_colored(f"ERROR: Could not import {name}: {e}", "red")
            failed_modules.append((name, str(e)))

    if failed_modules:
        print_colored(f"Failed to import {len(failed_modules)} modules in {package_name}:", "red")
        for module, error in failed_modules:
            print(f"  - {color(module, 'red')}: {error}")
        return False

    print_colored(
        f"Successfully imported all {len(all_modules)} modules in {package_name}", "green"
    )
    return True


def main() -> int:
    """Check all interdependencies between packages.

    Returns:
        0 if all checks pass, 1 otherwise.
    """
    success = True
    packages = ["dsbin", "dsbase"]

    print_colored("Checking package interdependencies...", "cyan")
    for pkg in packages:
        if not check_imports(pkg):
            success = False

    if success:
        print_colored("\nAll dependency checks passed! 🎉", "green")
    else:
        print_colored("\nSome dependency checks failed.", "red")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
