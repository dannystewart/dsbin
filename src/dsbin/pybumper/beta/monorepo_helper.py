"""Version management tool for Python projects."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.log import Logician

if TYPE_CHECKING:
    from logging import Logger


class MonorepoHelperBeta:
    """Helper for monorepo detection and package management."""

    logger: Logger = Logician.get_logger()

    @staticmethod
    def is_monorepo(directory: Path) -> bool:
        """Determine if a directory is part of a monorepo."""
        # Check for packages directory with multiple packages
        packages_dir = directory / "packages"
        if packages_dir.exists() and packages_dir.is_dir():
            # Count subdirectories that contain pyproject.toml
            package_count = sum(
                1 for d in packages_dir.iterdir() if d.is_dir() and (d / "pyproject.toml").exists()
            )
            if package_count > 1:
                return True

        # Check for monorepo configuration in pyproject.toml
        pyproject_path = directory / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib

                data = tomllib.loads(pyproject_path.read_text())
                if "tool" in data and "monorepo" in data["tool"]:
                    return True
            except (tomllib.TOMLDecodeError, KeyError):
                pass

        return False

    @classmethod
    def find_monorepo_root(cls, start_dir: Path) -> Path | None:
        """Find the root of the monorepo starting from a given directory."""
        current = start_dir
        # Limit the search to avoid going too far up
        for _ in range(5):
            if cls.is_monorepo(current):
                return current

            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent

        return None

    @classmethod
    def auto_detect_package(cls) -> tuple[str, Path]:
        """Try to determine the package from the current directory."""
        current_dir = Path.cwd()

        # Check if we're in a standard repository with pyproject.toml
        if (current_dir / "pyproject.toml").exists():
            # Check if this is a monorepo root
            if cls.is_monorepo(current_dir):
                # We're in a monorepo root
                main_package_name, main_package_path = cls._get_main_package_info(current_dir)

                if main_package_name and main_package_path:
                    return main_package_name, main_package_path

                # If we get here, we couldn't find the main package
                cls.logger.error(
                    "You're in a monorepo root. Please specify a package with --package."
                )
                sys.exit(1)

            # We're in a standard repository, so try to get the name from pyproject.toml
            package_name = cls._get_package_name_from_pyproject(current_dir / "pyproject.toml")
            if not package_name:
                package_name = current_dir.name

            package_path = current_dir
            return package_name, package_path

        # Check if we're in a package directory within a monorepo
        monorepo_root = cls.find_monorepo_root(current_dir)
        if monorepo_root:
            # We're somewhere in a monorepo

            # Check if we're in a package directory
            if (current_dir / "pyproject.toml").exists():
                # This directory has a pyproject.toml, likely a package
                package_name = cls._get_package_name_from_pyproject(current_dir / "pyproject.toml")
                if not package_name:
                    package_name = current_dir.name
                package_path = current_dir
                return package_name, package_path

            # Check if we're in the src directory of a package
            if current_dir.name == "src" and (current_dir.parent / "pyproject.toml").exists():
                package_name = cls._get_package_name_from_pyproject(
                    current_dir.parent / "pyproject.toml"
                )
                if not package_name:
                    package_name = current_dir.parent.name
                package_path = current_dir.parent
                return package_name, package_path

            cls.logger.error(
                "You're in a monorepo but not in a package directory. "
                "Please navigate to a package directory or use --package."
            )
            sys.exit(1)

        cls.logger.error("Could not auto-detect package. Please specify a package with --package.")
        sys.exit(1)

    @classmethod
    def _get_main_package_info(cls, monorepo_root: Path) -> tuple[str | None, Path | None]:
        """Extract main package information from monorepo root."""
        try:
            import tomllib

            pyproject_path = monorepo_root / "pyproject.toml"

            if not pyproject_path.exists():
                return None, None

            pyproject_data = tomllib.loads(pyproject_path.read_text())

            if "project" in pyproject_data and "name" in pyproject_data["project"]:
                main_package_name = pyproject_data["project"]["name"]

                # Check src directory for the package
                main_package_path = monorepo_root / "src" / main_package_name
                if main_package_path.exists():
                    return main_package_name, main_package_path

                # Check for kebab-case to snake_case conversion
                snake_case_path = monorepo_root / "src" / main_package_name.replace("-", "_")
                if snake_case_path.exists():
                    return main_package_name, snake_case_path
        except (tomllib.TOMLDecodeError, KeyError, FileNotFoundError) as e:
            cls.logger.debug("Error reading pyproject.toml: %s", e)

        return None, None

    @classmethod
    def _get_package_name_from_pyproject(cls, pyproject_path: Path) -> str | None:
        """Extract package name from pyproject.toml."""
        try:
            import tomllib

            pyproject_data = tomllib.loads(pyproject_path.read_text())

            if "project" in pyproject_data and "name" in pyproject_data["project"]:
                return pyproject_data["project"]["name"]
        except (tomllib.TOMLDecodeError, KeyError, FileNotFoundError) as e:
            cls.logger.debug("Error reading pyproject.toml: %s", e)

        return None

    @classmethod
    def find_package_in_monorepo(cls, package_name: str) -> tuple[str, Path]:
        """Find a package by name from the monorepo root."""
        current_dir = Path.cwd()

        # Try to find monorepo root
        monorepo_root = cls.find_monorepo_root(current_dir)
        if not monorepo_root:
            cls.logger.error("Could not find monorepo root. Please run from within a monorepo.")
            sys.exit(1)

        # Check if this is the main package
        main_package_name, main_package_path = cls._get_main_package_info(monorepo_root)

        if main_package_name == package_name and main_package_path:
            return package_name, main_package_path

        # Look for the package in common locations
        possible_paths = cls._get_possible_package_paths(monorepo_root, package_name)

        for path in possible_paths:
            if MonorepoHelperBeta.is_valid_package_path(path):
                return package_name, path

        cls.logger.error(
            "Could not find package '%s' in the monorepo. Searched in: %s",
            package_name,
            ", ".join(str(p) for p in possible_paths),
        )
        sys.exit(1)

    @classmethod
    def _get_possible_package_paths(cls, monorepo_root: Path, package_name: str) -> list[Path]:
        """Get all possible paths for a package in a monorepo."""
        possible_paths = [
            monorepo_root / "packages" / package_name,  # packages/name
            monorepo_root / "packages" / package_name / "src",  # packages/name/src
            monorepo_root / "src" / package_name,  # src/name
            monorepo_root / package_name,  # direct subdirectory
        ]

        # Also check for kebab-case to snake_case conversion
        snake_case_name = package_name.replace("-", "_")
        if snake_case_name != package_name:
            possible_paths.extend([
                monorepo_root / "packages" / snake_case_name,
                monorepo_root / "packages" / snake_case_name / "src",
                monorepo_root / "src" / snake_case_name,
                monorepo_root / snake_case_name,
            ])

        return possible_paths

    @classmethod
    def detect_package(cls, package_arg: str | None = None) -> tuple[str, Path]:
        """Detect package and relevant paths."""
        # Auto-detect package if not provided
        if package_arg is None:
            package_name, package_path = cls.auto_detect_package()
        else:
            # Try to find the package in a monorepo first
            current_dir = Path.cwd()
            monorepo_root = cls.find_monorepo_root(current_dir)

            if monorepo_root:
                package_name, package_path = cls.find_package_in_monorepo(package_arg)
            # Not in a monorepo, treat as standard repository
            elif (current_dir / "pyproject.toml").exists():
                package_name = package_arg
                package_path = current_dir
            else:
                cls.logger.error("Not in a repository with pyproject.toml.")
                sys.exit(1)

        # Verify package exists
        if not package_path.exists():
            cls.logger.error("Error: Package directory '%s' not found.", package_path)
            sys.exit(1)

        return package_name, package_path

    @staticmethod
    def is_valid_package_path(path: Path) -> bool:
        """Check if a path is a valid package directory."""
        return (
            path.exists()
            and path.is_dir()
            and ((path / "pyproject.toml").exists() or (path.parent / "pyproject.toml").exists())
        )
