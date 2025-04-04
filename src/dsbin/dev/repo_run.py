#!/usr/bin/env python3
"""Package management utility for working with multiple Poetry projects."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from polykit.parsers import print_color

# List of all your package directories
PACKAGES = [
    "dsbin",
    "enviromancer",
    "evremixes",
    "iplooker",
    "logician",
    "pathkeeper",
    "polykit",
    "walking-man",
]


def run_command(cmd: str, cwd: Path) -> int:
    """Run a shell command and return exit code, stdout, and stderr."""
    process = subprocess.run(cmd, shell=True, cwd=cwd, stdout=None, stderr=None, check=False)
    return process.returncode


def run_in_all(
    command: str, description: str, packages: list[str], base_dir: Path, clear_cache: bool = False
) -> None:
    """Run a command in all package directories."""
    print_color(f"\n===== {description} =====", "green")

    if clear_cache:
        print_color("\nClearing Poetry cache...", "yellow")
        run_command("poetry cache clear PyPI --all -n", base_dir)

    for pkg in packages:
        pkg_dir = base_dir / pkg

        if not pkg_dir.is_dir():
            print_color(f">>> Skipping {pkg} (directory not found)", "yellow")
            continue

        print_color(f"\n>>> Processing {pkg}...", "yellow")

        exit_code = run_command(command, pkg_dir)
        if exit_code == 0:
            print_color(f"\n✓ {pkg} completed successfully!", "green")
        else:
            print_color(f"\n>>> Error processing {pkg} (exit code: {exit_code})", "red")

    print_color("\n===== All operations completed! =====", "green")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Manage multiple Poetry packages")
    parser.add_argument(
        "command",
        choices=["update", "lock", "hooks", "status", "custom"],
        help="command to execute across packages",
    )
    parser.add_argument(
        "custom_command",
        nargs="?",
        help="custom command to run (required with 'custom')",
    )
    parser.add_argument(
        "--packages",
        nargs="+",
        default=PACKAGES,
        help="specific packages to process (defaults to all)",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="base directory containing package folders",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point for the package management utility."""
    args = parse_args()

    if args.command == "update":
        run_in_all(
            "poetry up --latest",
            "Updating dependencies to latest versions",
            args.packages,
            args.dir,
            clear_cache=True,
        )
    elif args.command == "lock":
        run_in_all(
            "poetry lock && poetry sync --all-extras --all-groups",
            "Locking and syncing dependencies",
            args.packages,
            args.dir,
        )
    elif args.command == "hooks":
        run_in_all(
            "pre-commit uninstall && pre-commit install",
            "Reinstalling pre-commit hooks",
            args.packages,
            args.dir,
        )
    elif args.command == "status":
        run_in_all("git status", "Checking Git status", args.packages, args.dir)
    elif args.command == "custom":
        if not args.custom_command:
            print_color("Error: Custom command requires a second argument", "red")
            return 1
        run_in_all(
            args.custom_command,
            f"Running custom command: {args.custom_command}",
            args.packages,
            args.dir,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
