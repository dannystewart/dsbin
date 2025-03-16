#!/usr/bin/env python3

"""Migrate Python packages between pyenv environments.

This script exports the packages from a source pyenv environment and installs them in a
target pyenv environment.
"""

from __future__ import annotations

import argparse
import os
import subprocess

from dsbase import configure_traceback

configure_traceback()


def run_command(command: str, env: dict[str, str]) -> None:
    """Run a shell command with a specified environment."""
    subprocess.run(command, shell=True, env=env, check=False)


def export_and_install_packages(source_env: str, target_env: str) -> None:
    """Export packages from source environment and install them in target environment."""
    get_packages(source_env, "pip freeze > requirements.txt")
    get_packages(target_env, "pip install -r requirements.txt")
    os.remove("requirements.txt")


def get_packages(env: str, command: str) -> None:
    """Set PYENV_VERSION to source environment and export packages."""
    env_source = os.environ.copy()
    env_source["PYENV_VERSION"] = env
    run_command(command, env_source)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Transfer Python packages between pyenv environments."
    )
    parser.add_argument("--source", required=True, help="Source pyenv environment name.")
    parser.add_argument("--target", required=True, help="Target pyenv environment name.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    export_and_install_packages(args.source, args.target)
