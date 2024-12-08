#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit

from dsutil import configure_traceback

if TYPE_CHECKING:
    from collections.abc import Sequence

configure_traceback()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Poetry pyproject.toml files to uv-compatible format"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually perform the conversion. Without this, only shows what would be converted",
    )

    # Create mutually exclusive group for path/file arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Directory path to search for pyproject.toml files (default: current directory)",
    )
    group.add_argument(
        "--file",
        type=Path,
        help="Single pyproject.toml file to convert",
    )

    return parser.parse_args(argv)


def parse_authors(authors: list[Any] | str | None) -> list[dict[str, str]]:
    """Parse authors from various possible Poetry formats into hatchling format."""
    if not authors:
        return []

    parsed = []

    if isinstance(authors, str):
        authors = [authors]

    for author in authors:
        if isinstance(author, str):
            # Parse "Name <email>" format
            if "<" in author and ">" in author:
                name, email = author.split("<", 1)
                email = email.rstrip(">")
                parsed.append({"name": name.strip(), "email": email.strip()})
            else:
                parsed.append({"name": author.strip()})
        elif isinstance(author, dict):
            author_entry = {"name": author.get("name", "").strip()}
            if email := author.get("email"):
                author_entry["email"] = email.strip()
            parsed.append(author_entry)

    return parsed


def convert_dependencies(deps: dict[str, Any]) -> list[str]:
    """Convert Poetry dependency specs to PEP 621 format."""
    converted = []
    for name, spec in deps.items():
        # Strip quotes from package name if present
        name = name.strip('"')

        if isinstance(spec, str):
            converted.append(f'{name}>={spec.replace("^", "")}')
        elif isinstance(spec, dict):
            if "version" in spec:
                converted.append(f'{name}>={spec["version"].replace("^", "")}')
    return converted


def convert_pyproject(file_path: Path) -> None:
    """Convert a Poetry pyproject.toml to uv-compatible format."""
    with open(file_path) as f:
        pyproject = tomlkit.load(f)

    # Copy basic metadata
    poetry_section = pyproject.get("tool", {}).get("poetry", {})
    if not poetry_section:
        msg = "No [tool.poetry] section found in pyproject.toml"
        raise ValueError(msg)

    project = {
        "name": poetry_section.get("name"),
        "dynamic": ["version"],  # Add dynamic version
        "description": poetry_section.get("description"),
    }

    # Handle authors
    if authors := parse_authors(poetry_section.get("authors")):
        project["authors"] = authors

    # Handle readme if present
    if "readme" in poetry_section:
        project["readme"] = poetry_section["readme"]

    # Convert dependencies
    if "dependencies" in poetry_section:
        if python_version := poetry_section["dependencies"].get("python", ""):
            project["requires-python"] = f'>={python_version.replace("^", "")}'
            deps = poetry_section["dependencies"].copy()
            deps.pop("python", None)
        else:
            deps = poetry_section["dependencies"]

        project["dependencies"] = convert_dependencies(deps)

    # Handle dev dependencies
    if "group" in poetry_section and "dev" in poetry_section["group"]:
        project["optional-dependencies"] = {
            "dev": convert_dependencies(poetry_section["group"]["dev"]["dependencies"])
        }

    # Create new pyproject structure
    new_pyproject = {
        "build-system": {"requires": ["hatchling"], "build-backend": "hatchling.build"},
        "project": project,
    }

    # Add package configuration
    project_name = project["name"]

    # Initialize tool.hatch section
    new_pyproject["tool"] = {
        "hatch": {
            "version": {
                "path": "__init__.py"  # Add version path
            },
            "build": {"targets": {"wheel": {"packages": [project_name]}}},
        }
    }

    # If src layout is detected, adjust the packages path
    if (Path.cwd() / "src" / project_name).exists():
        new_pyproject["tool"]["hatch"]["version"]["path"] = f"src/{project_name}/__init__.py"
        new_pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] = [
            f"src/{project_name}"
        ]
    elif not (Path.cwd() / project_name).exists():
        print(
            f"Warning: Could not find package directory for {project_name}. "
            "Package configuration might need manual adjustment."
        )

    # Write back to file
    with open(file_path, "w") as f:
        tomlkit.dump(new_pyproject, f)


def find_pyproject_files(start_path: Path) -> list[Path]:
    """Find all pyproject.toml files under the start path."""
    return sorted(start_path.rglob("pyproject.toml"))


def validate_file(file_path: Path) -> None:
    """Validate that the file exists and is a pyproject.toml file."""
    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)
    if file_path.name != "pyproject.toml":
        msg = f"File must be named 'pyproject.toml', got: {file_path.name}"
        raise ValueError(msg)


def main(argv: Sequence[str] | None = None) -> int:
    """Process pyproject.toml file(s) based on command line arguments."""
    args = parse_args(argv)

    try:
        # Handle single file conversion
        if args.file:
            try:
                validate_file(args.file)
                print(f"Found pyproject.toml file: {args.file}")

                if not args.confirm:
                    print("\nRun with --confirm to perform the conversion")
                    return 0

                print("\nPerforming conversion...")
                convert_pyproject(args.file)
                print("Conversion complete!")
                return 0

            except (FileNotFoundError, ValueError) as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

        # Handle directory scanning
        pyproject_files = find_pyproject_files(args.path)

        if not pyproject_files:
            print(f"No pyproject.toml files found under {args.path}")
            return 1

        print("Found the following pyproject.toml files:")
        for file in pyproject_files:
            rel_path = file.relative_to(args.path)
            print(f"  {rel_path}")

        if not args.confirm:
            print("\nRun with --confirm to perform the conversion")
            return 0

        print("\nPerforming conversion...")
        for file in pyproject_files:
            rel_path = file.relative_to(args.path)
            print(f"Converting {rel_path}")
            convert_pyproject(file)

        print("\nConversion complete!")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
