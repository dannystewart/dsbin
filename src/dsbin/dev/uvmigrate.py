#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit
from polykit import polykit_setup

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tomlkit.items import Table

polykit_setup()


def find_pyproject_files(start_path: Path) -> list[Path]:
    """Find all pyproject.toml files under the start path."""
    return sorted(start_path.rglob("pyproject.toml"))


def validate_file(file_path: Path) -> None:
    """Validate that the file exists and is a pyproject.toml file.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the file is not named 'pyproject.toml'.
    """
    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)
    if file_path.name != "pyproject.toml":
        msg = f"File must be named 'pyproject.toml', got: {file_path.name}"
        raise ValueError(msg)


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
            if email := author.get("email", ""):
                author_entry["email"] = email.strip()
            parsed.append(author_entry)

    return parsed


def create_basic_project(poetry_section: dict) -> dict:
    """Create basic project metadata from Poetry section."""
    project = {
        "name": poetry_section.get("name"),
        "description": poetry_section.get("description"),
    }

    if version := poetry_section.get("version"):
        project["version"] = version

    if authors := parse_authors(poetry_section.get("authors")):
        authors_array = tomlkit.array()
        authors_array.multiline(False)
        for author in authors:
            author_item = tomlkit.inline_table()
            author_item.update(author)
            authors_array.append(author_item)
        project["authors"] = authors_array

    if "readme" in poetry_section:
        project["readme"] = poetry_section["readme"]

    return project


def _convert_git_dependency_to_pep508(name: str, spec: dict[str, Any]) -> str:
    """Convert a git dependency to PEP 508 format."""
    git_url = spec["git"]
    rev = None
    if "branch" in spec:
        rev = spec["branch"]
    if "tag" in spec:
        rev = spec["tag"]
    if "rev" in spec:
        rev = spec["rev"]

    pep508_ref = f"{name} @ git+{git_url}"
    if rev:
        pep508_ref += f"@{rev}"
    return pep508_ref


def _convert_regular_dependency(
    name: str, spec: dict[str, Any] | str, dev_group: bool = False
) -> str:
    """Convert a regular (non-git) dependency specification."""
    if dev_group:
        return name

    if isinstance(spec, dict) and "version" in spec:
        version = spec["version"].replace("^", "")
    else:
        version = str(spec).replace("^", "")

    version = version.removeprefix(">=")
    return f"{name}>={version}"


def convert_dependencies(
    deps: dict[str, Any], multiline: bool = True, dev_group: bool = False
) -> tuple[list[str], dict[str, dict]]:
    """Convert Poetry dependency specs to PEP 621 format."""
    converted = tomlkit.array()
    converted.multiline(multiline)
    converted.indent(4)
    sources = tomlkit.table()

    # Convert and sort dependencies
    dep_list = []
    for name, spec in sorted(deps.items()):
        name = name.strip('"')

        if isinstance(spec, dict) and "git" in spec:
            pep508_ref = _convert_git_dependency_to_pep508(name, spec)
            dep_list.append(pep508_ref)
            continue

        dep_list.append(_convert_regular_dependency(name, spec, dev_group))

    # Add sorted dependencies to the array
    for dep in sorted(dep_list):
        converted.append(dep)

    return converted, sources


def convert_git_dependency(
    name: str, spec: dict[str, Any]
) -> tuple[str, dict[str, Any], str] | None:
    """Convert a Poetry git dependency to both uv and PEP 508 formats."""
    if "git" in spec:
        git_url = spec["git"]
        source = {"git": git_url}

        # Handle revision specifications
        rev = None
        if "branch" in spec:
            rev = spec["branch"]
            source["rev"] = rev
        if "tag" in spec:
            rev = spec["tag"]
            source["rev"] = rev
        if "rev" in spec:
            rev = spec["rev"]
            source["rev"] = rev

        # Create PEP 508 direct reference
        pep508_ref = f"{name} @ git+{git_url}"
        if rev:
            pep508_ref += f"@{rev}"

        return name, source, pep508_ref
    return None


def handle_dependencies(poetry_section: dict, project: dict) -> None:
    """Process and add all dependencies to the project."""
    if "dependencies" in poetry_section:
        if python_version := poetry_section["dependencies"].get("python", ""):
            cleaned_version = python_version.replace("^", "")
            project["requires-python"] = (
                cleaned_version
                if any(op in cleaned_version for op in (">=", "<=", "<", ">", "==", "!="))
                else f">={cleaned_version}"
            )
            deps = poetry_section["dependencies"].copy()
            deps.pop("python", None)
        else:
            deps = poetry_section["dependencies"]

        project["dependencies"], _ = convert_dependencies(deps, multiline=False)


def handle_dev_dependencies(poetry_section: dict) -> Table | None:
    """Process and add development dependencies to the project."""
    if "group" in poetry_section and "dev" in poetry_section["group"]:
        dev_deps, _ = convert_dependencies(
            poetry_section["group"]["dev"]["dependencies"], multiline=True, dev_group=True
        )
        dep_groups = tomlkit.table()
        dep_groups["dev"] = dev_deps
        return dep_groups
    return None


def adjust_src_layout(project_name: str, new_pyproject: dict) -> None:
    """Adjust configuration for src layout if detected."""
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


def backup_file(file_path: Path) -> Path:
    """Create a backup of the original file."""
    backup_path = file_path.with_suffix(file_path.suffix + ".old")

    # If .old already exists, add a number
    counter = 1
    while backup_path.exists():
        backup_path = file_path.with_suffix(f"{file_path.suffix}.old{counter}")
        counter += 1

    backup_path.write_text(file_path.read_text())
    return backup_path


def convert_pyproject(file_path: Path) -> None:
    """Convert a Poetry pyproject.toml to uv-compatible format.

    Raises:
        ValueError: If the file does not contain a [tool.poetry] section.
    """
    # Create backup first
    backup_path = backup_file(file_path)
    print(f"Backup created at: {backup_path}")

    with Path(file_path).open(encoding="utf-8") as f:
        pyproject = tomlkit.load(f)

    poetry_section = pyproject.get("tool", {}).get("poetry", {})
    if not poetry_section:
        msg = "No [tool.poetry] section found in pyproject.toml"
        raise ValueError(msg)

    # Create document with ordered sections
    new_pyproject = tomlkit.document()

    # 1. Build system
    new_pyproject["build-system"] = {"requires": ["hatchling"], "build-backend": "hatchling.build"}

    # 2. Project section and its immediate children
    project = create_basic_project(poetry_section)

    # Handle dependencies
    handle_dependencies(poetry_section, project)

    # Add complete project section
    new_pyproject["project"] = project

    # Add dependency groups if they exist
    if dep_groups := handle_dev_dependencies(poetry_section):
        new_pyproject["dependency-groups"] = dep_groups

    # 3. Tool section
    tool_section = tomlkit.table()

    # 3a. Hatch configuration
    hatch_config = {
        "version": {"path": "__init__.py"},
        "build": {"targets": {"wheel": {"packages": [project["name"]]}}},
        "metadata": {"allow-direct-references": True},
    }
    tool_section["hatch"] = hatch_config
    new_pyproject["tool"] = tool_section

    # Adjust src layout if needed
    adjust_src_layout(project["name"], new_pyproject)

    # Store original scripts section text
    scripts_text = ""
    if "scripts" in poetry_section:
        with Path(file_path).open(encoding="utf-8") as f:
            content = f.read()
            # Find the [tool.poetry.scripts] section
            if "[tool.poetry.scripts]" in content:
                scripts_part = content.split("[tool.poetry.scripts]")[1]
                # Get everything up to the next section or end of file
                scripts_text = scripts_part.split("\n[")[0]

    # Write main configuration
    with Path(file_path).open("w", encoding="utf-8") as f:
        tomlkit.dump(new_pyproject, f)

    # Add scripts section with original formatting if it exists
    if scripts_text:
        with Path(file_path).open("a", encoding="utf-8") as f:
            f.write("\n[project.scripts]")
            f.write(scripts_text)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="convert Poetry pyproject.toml files to uv-compatible format"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="perform conversion (without this, only dry run)"
    )

    # Create mutually exclusive group for path/file arguments
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--path",
        type=Path,
        default=Path(),
        help="directory to search for pyproject.toml files (default: current dir)",
    )
    group.add_argument("--file", type=Path, help="single pyproject.toml file to convert")

    return parser.parse_args(argv)


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
