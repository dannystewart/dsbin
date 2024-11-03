#!/usr/bin/env python3

"""
Create a list of script aliases to ensure the right venv.

This script will create a file with aliases for all the executable files in the target directories.
The aliases will ensure that the right Python virtual environment is used when running the scripts.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from dsutil.text import color, print_colored

# Bin directory (for executable scripts to run from)
BIN_DIR = os.path.expanduser("~/.local/bin")
TARGET_DIRS = [BIN_DIR]

# Aliases file (to store the aliases for the executable scripts)
ALIASES_FILE = os.path.expanduser("~/.aliases_scripts")

# Files and extensions to exclude from the list of executables to create aliases for
EXCLUDED_FILES = ["envscripts", "pip", "pip3", "poetry", "python", "python3", "updater"]
EXCLUDED_EXTENSIONS = {".sh"}

# Critical dependencies and minimum versions (or None for latest)
CRITICAL_DEPENDENCIES = {
    "termcolor": None,
}


def _print_header(message: str) -> None:
    print_colored(f"\n{message}:", "cyan")


def _check_passed(message: str) -> None:
    print_colored(f"✓ {message}", "green")


def _check_failed(message: str) -> None:
    print_colored(f"✗ {message}", "red")


def perform_health_check(verbose: bool = False) -> None:
    """Perform a comprehensive health check of the script environment and setup."""
    # Check script location
    script_path = os.path.realpath(sys.argv[0])
    _print_header("Script Location")
    _check_passed(f"Running from: {script_path}")

    python_installs_check = _check_python_installations()
    source_target_check = _check_source_and_target()
    venv_python_check = _check_venv_python()
    dsutil_check = _check_dsutil_versions()
    aliases_scripts_check = _check_aliases_and_scripts(verbose)

    checks_passed = (
        python_installs_check
        and source_target_check
        and venv_python_check
        and dsutil_check
        and aliases_scripts_check
    )

    # Final status
    _print_header("Overall Status")
    if checks_passed:
        _check_passed("All checks passed successfully")
    else:
        _check_failed("Some checks failed - see details above")


def _check_venv_python() -> bool:
    """Check Python version and key dependencies in the venv."""
    checks_passed = True

    _print_header("Virtual Environment Python")

    venv_path = get_poetry_venv_path(verbose=False)
    if not venv_path:
        _check_failed("Could not determine Poetry venv path")
        return False

    # Get Python version from venv
    python_path = os.path.join(venv_path, "bin", "python")
    try:
        result = subprocess.run([python_path, "-V"], capture_output=True, text=True, check=True)
        _check_passed(f"Venv Python version: {result.stdout.strip()}")
        _check_passed(f"Venv Python: {python_path}")

        # Check current Python but don't count it as a failure
        current_python = sys.executable
        if current_python == python_path:
            _print_header(
                "NOTE: Script is running from the venv Python (may not be desired behavior)"
            )
        else:
            _print_header("Script is running from system Python (expected behavior)")
            _check_passed(f"System Python: {current_python}")

            # Check dependencies in both environments
            _print_header("System Python Dependencies")
            try:
                result = subprocess.run(
                    [current_python, "-m", "pip", "list"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                sys_packages = {
                    line.split()[0].lower(): line.split()[1]
                    for line in result.stdout.splitlines()[2:]
                }

                if "termcolor" in sys_packages:
                    _check_passed(
                        f"Found termcolor {sys_packages['termcolor']} (used by this script)"
                    )
                else:
                    _check_failed("Missing termcolor (needed for this script's output)")
                    checks_passed = False
            except subprocess.CalledProcessError:
                _check_failed("Failed to check system Python packages")
                checks_passed = False

    except subprocess.CalledProcessError:
        checks_passed = False
        _check_failed("Failed to get Python version from venv")

    # Check venv dependencies (for managed scripts)
    _print_header("Venv Dependencies (used by managed scripts)")
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "list"], capture_output=True, text=True, check=True
        )

        packages = {
            line.split()[0].lower(): line.split()[1] for line in result.stdout.splitlines()[2:]
        }

        # Check PyPI packages
        if "termcolor" in packages:
            _check_passed(f"Found termcolor {packages['termcolor']}")
        else:
            checks_passed = False
            _check_failed("Missing termcolor - Required for colored output in managed scripts")

        # Check for dsutil as a local module
        try:
            result = subprocess.run(
                [python_path, "-c", "import dsutil; print('ok')"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout.strip() == "ok":
                _check_passed("Local dsutil module is importable")
            else:
                checks_passed = False
                _check_failed("Local dsutil module import check failed")
        except subprocess.CalledProcessError:
            checks_passed = False
            _check_failed("Local dsutil module not found in Python path")

    except subprocess.CalledProcessError:
        checks_passed = False
        _check_failed("Failed to check venv packages")

    return checks_passed


def _check_python_installations() -> bool:
    """Check and report on Python installations from different sources."""
    _print_header("Installed Python Versions")

    try:  # Check system Python
        result = subprocess.run(
            ["/usr/bin/python3", "-V"], capture_output=True, text=True, check=True
        )
        _check_passed(f"{color("System Python:", "green")} {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("No system Python found in /usr/bin")

    try:  # Check Homebrew Pythons
        _check_homebrew_python()

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Homebrew not found or not accessible")

    try:  # Check pyenv Pythons
        _check_pyenv_python()

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pyenv not found or not accessible")

    return True


def _check_homebrew_python() -> None:
    brew_cellar = subprocess.run(
        ["brew", "--cellar"], capture_output=True, text=True, check=True
    ).stdout.strip()

    python_versions = []
    for version in ["python@3", "python@3.12", "python@3.13"]:
        python_path = os.path.join(brew_cellar, version)
        if os.path.exists(python_path):
            try:
                brew_python = os.path.join("/opt/homebrew/bin", "python3")
                if version != "python@3":
                    brew_python = f"{brew_python}.{version.split('.')[-1]}"

                result = subprocess.run(
                    [brew_python, "-V"], capture_output=True, text=True, check=True
                )
                python_versions.append(f"{version}: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                python_versions.append(f"{version}: installed but version check failed")

    if python_versions:
        _check_passed("Homebrew Python installations:")
        for version in python_versions:
            print(f"  - {version}")
    else:
        print("No Homebrew Python installations found")


def _check_pyenv_python() -> None:
    result = subprocess.run(["pyenv", "versions"], capture_output=True, text=True, check=True)
    if versions := [
        line.strip().replace("* ", "")  # Remove the * from current version
        for line in result.stdout.splitlines()
        if line.strip() and line.strip() != "system"  # Skip empty lines and system
    ]:
        _check_passed("pyenv Python installations:")
        current = subprocess.run(
            ["pyenv", "version"], capture_output=True, text=True, check=True
        ).stdout.split()[0]

        for version in versions:
            # Strip any parenthetical information for the comparison
            clean_version = version.split(" (")[0]
            if clean_version == current:
                print(f"  ✓ {version}")
            else:
                print(f"  - {version}")
    else:
        print("No pyenv Python installations found")


def _check_dsutil_versions() -> bool:
    """Check dsutil versions across different installations."""
    checks_passed = True

    _print_header("dsutil Versions")

    # Check system-level dsutil
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "dsutil"],
            capture_output=True,
            text=True,
            check=True,
        )
        system_version = next(
            line.split(": ")[1]
            for line in result.stdout.splitlines()
            if line.startswith("Version: ")
        )
        _check_passed(f"System installation: {system_version}")
    except (subprocess.CalledProcessError, StopIteration):
        _check_failed("dsutil not installed at system level")
        checks_passed = False

    if venv_path := get_poetry_venv_path(verbose=False):
        python_path = os.path.join(venv_path, "bin", "python")
        try:
            result = subprocess.run(
                [python_path, "-m", "pip", "show", "dsutil"],
                capture_output=True,
                text=True,
                check=True,
            )
            venv_version = next(
                line.split(": ")[1]
                for line in result.stdout.splitlines()
                if line.startswith("Version: ")
            )
            _check_passed(f"Poetry venv installation: {venv_version}")
        except (subprocess.CalledProcessError, StopIteration):
            _check_failed("dsutil not installed in Poetry venv")
            checks_passed = False

    return checks_passed


def _check_source_and_target() -> bool:
    checks_passed = True

    # Check if poetry is installed and get version
    _print_header("Poetry Status")
    result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        _check_passed(f"Poetry installed: {result.stdout.strip()}")
    else:
        _check_failed("Poetry not found or not working")
        checks_passed = False

    # Check target directories
    _print_header("Target Directories")
    for dir_path in TARGET_DIRS:
        expanded_path = os.path.expanduser(dir_path)
        if os.path.isdir(expanded_path):
            _check_passed(f"{dir_path} exists")
            # Check directory permissions
            if os.access(expanded_path, os.W_OK):
                _check_passed(f"{dir_path} is writable")
            else:
                checks_passed = False
                _check_failed(f"{dir_path} is not writable")
        else:
            checks_passed = False
            _check_failed(f"{dir_path} does not exist")

    return checks_passed


def _check_aliases_and_scripts(verbose: bool = False) -> bool:
    checks_passed = True

    # Check aliases file
    _print_header("Aliases File")
    if os.path.exists(ALIASES_FILE):
        _check_passed(f"Exists at: {ALIASES_FILE}")
        try:
            with open(ALIASES_FILE, encoding="utf-8") as f:
                content = f.read()
                # Extract venv path from aliases file
                import re

                if venv_match := re.search(r"VENV_PYTHON='(.+?)/bin/python'", content):
                    stored_venv_path = venv_match.group(1)
                    _check_passed(f"Stored venv path: {stored_venv_path}")

                    # Compare with current poetry venv
                    current_venv = get_poetry_venv_path(verbose=False)
                    if stored_venv_path == current_venv:
                        _check_passed("Stored venv matches current Poetry venv")
                    else:
                        checks_passed = False
                        _check_failed("Stored venv differs from current Poetry venv:")
                        print(f"  Stored: {stored_venv_path}")
                        print(f"  Current: {current_venv}")
                else:
                    checks_passed = False
                    _check_failed("Could not find venv path in aliases file")
        except Exception as e:
            checks_passed = False
            _check_failed(f"Error reading aliases file: {e}")
    else:
        checks_passed = False
        _check_failed("Aliases file does not exist")

    # Check executable files
    _print_header("Executable Scripts")
    if exec_files := get_executable_files(TARGET_DIRS):
        _check_passed(f"Found {len(exec_files)} executable scripts")
        if verbose:
            for exec_file in exec_files:
                print(f"  - {os.path.basename(exec_file)}")
    else:
        checks_passed = False
        _check_failed("No executable scripts found")

    return checks_passed


def _install_critical_deps() -> bool:
    """Install critical dependencies in the system Python environment."""
    _print_header("Installing Critical Dependencies")

    current_python = sys.executable
    success = True

    # Get current packages in system Python
    try:
        result = subprocess.run(
            [current_python, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
        installed_packages = {
            line.split()[0].lower(): line.split()[1] for line in result.stdout.splitlines()[2:]
        }
    except subprocess.CalledProcessError:
        _check_failed("Failed to check current packages")
        return False

    # Install missing packages
    for package, min_version in CRITICAL_DEPENDENCIES.items():
        if package not in installed_packages:
            try:
                install_cmd = [current_python, "-m", "pip", "install", package]
                if min_version:
                    install_cmd[-1] = f"{package}>={min_version}"

                _check_passed(f"Installing {package}...")
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                _check_passed(f"Successfully installed {package}")

            except subprocess.CalledProcessError as e:
                _check_failed(f"Failed to install {package}: {e.stderr}")
                success = False
        else:
            print(f"✓ {package} is already installed ({installed_packages[package]})")

    try:
        update_dsutil()
    except subprocess.CalledProcessError as e:
        _check_failed(f"Failed to update dsutil: {e.stderr}")
        success = False

    return success


def update_dsutil(verbose: bool = True) -> bool:
    """Update dsutil in both system and Poetry environments."""
    success = True

    if verbose:
        _print_header("Updating dsutil")

    try:  # Update system-level installation
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "git+https://gitlab.dannystewart.com/danny/dsutil.git",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose:
            _check_passed("System-level dsutil updated")
    except subprocess.CalledProcessError as e:
        _check_failed(f"Failed to update system-level dsutil: {e.stderr}")
        success = False

    try:  # Update Poetry venv installation
        subprocess.run(
            ["poetry", "update", "dsutil"],
            check=True,
            capture_output=True,
            text=True,
            cwd=BIN_DIR,
        )
        if verbose:
            _check_passed("Poetry venv dsutil updated")
    except subprocess.CalledProcessError as e:
        _check_failed(f"Failed to update Poetry venv dsutil: {e.stderr}")
        success = False

    return success


def is_poetry_installed(verbose: bool = False) -> bool:
    """Check if Poetry is installed and accessible."""
    result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
    if verbose:
        print_colored("Poetry is installed: ", "cyan", end="")
        print(result.stdout)
    return result.returncode == 0


def get_poetry_venv_path(verbose: bool = False) -> str:
    """Return the path to the Poetry virtual environment or exit the script if not found."""
    result = subprocess.run(
        ["poetry", "env", "info", "-p"], capture_output=True, text=True, cwd=BIN_DIR
    )
    if verbose:
        print_colored("Poetry venv path:", "cyan")
        print(result.stdout)
    if result.returncode != 0:
        print_colored(f"Failed to get Poetry virtual environment path: {result.stderr}", "red")
        print_colored("Try running cdbin > poetry env use > poetry install.", "yellow")
        sys.exit(1)
    return result.stdout.strip()


def python_executable_exists(venv_path: str, verbose: bool = False) -> bool:
    """Check if the Python executable exists in the virtual environment."""
    if sys.platform.startswith("win"):
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
    if verbose:
        print_colored("Using Python path:", "cyan")
        print(f"{python_path}\n")
    return os.path.exists(python_path)


def validate_target_dirs(target_dirs: list) -> None:
    """Ensure target directories exist and optionally contain executables."""
    for dir_path in target_dirs:
        if not os.path.isdir(dir_path):
            print_colored(f"Directory does not exist: {dir_path}", "red")
            sys.exit(1)


def get_executable_files(target_dirs: list) -> list:
    """Return a list of all the executable files in the target directories."""
    exec_files = []

    for dir_path in target_dirs:
        if os.path.isdir(dir_path):
            files = sorted(
                f
                for f in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, f))
                and os.access(os.path.join(dir_path, f), os.X_OK)
                and os.path.splitext(f)[1] not in EXCLUDED_EXTENSIONS
                and f not in EXCLUDED_FILES
            )
            for file in files:
                filepath = os.path.join(dir_path, file)
                exec_files.append(filepath)

    return exec_files


def create_aliases_file(exec_files: list, venv_path: str, verbose: bool = False) -> None:
    """
    Create a file with a list of aliases for the executable files.

    Args:
        exec_files: List of executable files to create aliases for.
        venv_path: Path to the Python virtual environment.
        verbose: Whether to print verbose output. Defaults to False.
    """
    try:
        with open(ALIASES_FILE, "w", encoding="utf-8") as f:
            f.write("# shellcheck disable=SC2139\n\n")
            f.write(f"VENV_PYTHON='{venv_path}/bin/python'\n")
            f.write(f"BIN_DIR='{BIN_DIR}'\n\n")

            for exec_file in exec_files:
                file_name = os.path.basename(exec_file)
                alias_cmd = f'alias {file_name}="$VENV_PYTHON $BIN_DIR/{file_name}"\n'
                f.write(alias_cmd)
                if verbose:
                    print_colored(
                        f"Created alias for {file_name} -> {venv_path}/{file_name}\n",
                        "cyan",
                        end="",
                    )
    except OSError as e:
        print_colored(f"Failed to write to {ALIASES_FILE}: {e}", "red")
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-a",
        "--auto",
        action="store_true",
        help="run in auto mode (no user interaction)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable verbose output",
    )
    parser.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="perform a health check of the current setup",
    )
    parser.add_argument(
        "-i",
        "--install-deps",
        action="store_true",
        help="install critical dependencies in system Python environment",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="update dsutil in all environments",
    )
    return parser.parse_args()


def main() -> None:
    """Update shell aliases based on current scripts."""
    args = parse_arguments()
    verbose = args.verbose

    # Perform health check if requested
    if args.check:
        perform_health_check(verbose)
        return

    # Update dsutil if requested
    if args.update:
        if update_dsutil():
            _check_passed("dsutil updated successfully")
        else:
            _check_failed("Some dsutil updates failed")
        return

    # Install critical dependencies if requested
    if args.install_deps:
        if _install_critical_deps():
            _check_passed("All critical dependencies installed successfully")
        else:
            _check_failed("Some dependencies failed to install")
        return

    # Check if Poetry is installed
    if not is_poetry_installed(verbose):
        print_colored("Poetry is not installed or not found in PATH.", "red")
        sys.exit(1)

    # Get the path to the Poetry virtual environment
    venv_path = get_poetry_venv_path(verbose)

    # Check if the Python executable exists in the virtual environment
    if not python_executable_exists(venv_path, verbose):
        print_colored("Python executable in the virtual environment not found.", "red")
        sys.exit(1)

    # Get the list of target directories and validate them
    target_dirs = [os.path.expanduser(d) for d in TARGET_DIRS]
    validate_target_dirs(target_dirs)

    # Get the list of executable files in the target directories
    exec_files = get_executable_files(target_dirs)

    # Create the aliases file
    create_aliases_file(exec_files, venv_path, verbose)

    if not args.auto:  # Print reminder if not in auto mode, shorten path for display purposes
        display_path = os.path.relpath(ALIASES_FILE, os.path.expanduser("~"))
        display_path = f"~/{display_path}" if not display_path.startswith("..") else display_path

        print_colored("\nScript aliases updated! Don't forget to source the file:", "green")
        print(f"source {display_path}")


if __name__ == "__main__":
    main()
