from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import tomlkit
from polykit.core import polykit_setup
from polykit.log import Logician
from tomlkit.items import Array

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tomlkit.items import Array

polykit_setup()

POETRY_TO_PEP621_MAPPING = {
    "name": "name",
    "version": "version",
    "description": "description",
    "authors": "authors",
    "readme": "readme",
    "license": "license",
    "homepage": "urls.homepage",
    "repository": "urls.repository",
    "documentation": "urls.documentation",
    "keywords": "keywords",
    "classifiers": "classifiers",
}

# Fields that should stay in tool.poetry
POETRY_SPECIFIC_FIELDS = {
    "packages",
    "plugins",
    "scripts",
    "group",
    "extras",
}

logger = Logician.get_logger(simple=True)


def find_pyproject_files(start_path: Path) -> list[Path]:
    """Find all pyproject.toml files under the start path."""
    return sorted(start_path.rglob("pyproject.toml"))


def validate_file(file_path: Path) -> None:
    """Validate that the file exists and is a pyproject.toml file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not named 'pyproject.toml'.
    """
    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)
    if file_path.name != "pyproject.toml":
        msg = f"File must be named 'pyproject.toml', got: {file_path.name}"
        raise ValueError(msg)


def parse_authors(authors: list[Any] | str | None) -> Array:
    """Parse authors from various possible Poetry formats into PEP 621 format."""
    if not authors:
        return tomlkit.array()

    parsed = tomlkit.array()
    parsed.multiline(False)

    if isinstance(authors, str):
        authors = [authors]

    for author in authors:
        author_table = tomlkit.inline_table()
        if isinstance(author, str):
            # Parse "Name <email>" format
            if "<" in author and ">" in author:
                name, email = author.split("<", 1)
                email = email.rstrip(">")
                author_table["name"] = name.strip()
                author_table["email"] = email.strip()
            else:
                author_table["name"] = author.strip()
        elif isinstance(author, dict):
            author_table["name"] = author.get("name", "").strip()
            if email := author.get("email", ""):
                author_table["email"] = email.strip()

        parsed.append(author_table)

    return parsed


def create_basic_project(poetry_section: dict[str, Any]) -> dict[str, Any]:
    """Create basic project metadata from Poetry section."""
    project = {}

    # Map standard fields
    for poetry_field, pep621_field in POETRY_TO_PEP621_MAPPING.items():
        if poetry_field in poetry_section:
            if "." in pep621_field:
                # Handle nested fields (like urls.homepage)
                parent, child = pep621_field.split(".")
                if parent not in project:
                    project[parent] = {}
                project[parent][child] = poetry_section[poetry_field]
            else:
                project[pep621_field] = poetry_section[poetry_field]

    # Handle authors specially due to format differences
    if "authors" in poetry_section:
        project["authors"] = parse_authors(poetry_section["authors"])

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


def _convert_regular_dependency(name: str, spec: dict[str, Any] | str) -> str:
    """Convert a regular dependency specification."""
    if isinstance(spec, dict) and "version" in spec:
        version = spec["version"].replace("^", "")
    else:
        version = str(spec).replace("^", "")

    version = version.removeprefix(">=")
    return f"{name}>={version}"


def convert_dependencies(deps: dict[str, Any]) -> Array:
    """Convert Poetry dependency specs to PEP 621 format."""
    converted = tomlkit.array()
    converted.multiline(True)
    converted.indent(4)

    # Convert and sort dependencies
    dep_list = []
    for name, spec in sorted(deps.items()):
        name = name.strip('"')

        if isinstance(spec, dict) and "git" in spec:
            pep508_ref = _convert_git_dependency_to_pep508(name, spec)
            dep_list.append(pep508_ref)
            continue

        dep_list.append(_convert_regular_dependency(name, spec))

    # Add sorted dependencies to the array
    for dep in sorted(dep_list):
        converted.append(dep)

    return converted


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


def clean_python_version(version: str) -> str:
    """Clean and format Python version requirement."""
    cleaned = version.replace("^", "")
    return (
        cleaned
        if any(op in cleaned for op in (">=", "<=", "<", ">", "==", "!="))
        else f">={cleaned}"
    )


def has_complex_dependencies(deps: dict[str, Any]) -> bool:
    """Check if dependencies contain complex Poetry-specific features."""
    return any(
        isinstance(spec, dict) and any(key in spec for key in ("git", "path", "url", "extras"))
        for spec in deps.values()
    )


def convert_simple_dependencies(deps: dict[str, Any]) -> Array:
    """Convert simple dependencies to project.dependencies format."""
    converted = tomlkit.array()
    converted.multiline(True)

    for name, spec in sorted(deps.items()):
        if isinstance(spec, str):
            converted.append(f'{name} = "{spec}"')
        elif isinstance(spec, dict) and "version" in spec:
            converted.append(f'{name} = "{spec["version"]}"')

    return converted


def handle_dev_dependencies(poetry_section: dict[str, Any], project: dict[str, Any]) -> None:
    """Handle development dependencies."""
    if "group" in poetry_section and "dev" in poetry_section["group"]:
        if "optional-dependencies" not in project:
            project["optional-dependencies"] = {}
        project["optional-dependencies"]["dev"] = poetry_section["group"]["dev"]["dependencies"]


def handle_dependencies(poetry_section: dict[str, Any], project: dict[str, Any]) -> None:
    """Process and add dependencies to the project."""
    if "dependencies" not in poetry_section:
        return

    deps = poetry_section["dependencies"].copy()

    # Handle Python version requirement
    if python_version := deps.pop("python", None):
        cleaned_version = python_version.replace("^", "")
        project["requires-python"] = (
            cleaned_version
            if any(op in cleaned_version for op in (">=", "<=", "<", ">", "==", "!="))
            else f">={cleaned_version}"
        )

    # Convert all dependencies to project.dependencies
    project["dependencies"] = convert_dependencies(deps)

    # Handle dev dependencies
    if "group" in poetry_section and "dev" in poetry_section["group"]:
        dev_deps = poetry_section["group"]["dev"]["dependencies"]
        if dev_deps:
            project.setdefault("optional-dependencies", {})["dev"] = convert_dependencies(dev_deps)


def adjust_src_layout(project_name: str, new_pyproject: dict[str, Any]) -> None:
    """Adjust configuration for src layout if detected."""
    if (Path.cwd() / "src" / project_name).exists():
        new_pyproject["tool"]["hatch"]["version"]["path"] = f"src/{project_name}/__init__.py"
        new_pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] = [
            f"src/{project_name}"
        ]
    elif not (Path.cwd() / project_name).exists():
        logger.warning(
            "Could not find package directory for %s. Package configuration might need manual adjustment.",
            project_name,
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


def extract_scripts_section(content: str) -> tuple[str, str | None]:
    """Extract the scripts section while preserving formatting and comments."""
    if "[tool.poetry.scripts]" not in content:
        return content, None

    parts = content.split("[tool.poetry.scripts]")
    before = parts[0]
    after = parts[1]

    # Find where the next section starts (if any)
    next_section = after.find("\n[")
    if next_section != -1:
        scripts = after[:next_section]
        remaining = after[next_section:]
    else:
        scripts = after
        remaining = ""

    return before + remaining, scripts


def convert_pyproject(file_path: Path) -> None:
    """Convert a Poetry pyproject.toml to Poetry 2.0 format.

    Raises:
        ValueError: If no [tool.poetry] section is found.
    """
    # Create backup first
    backup_path = backup_file(file_path)
    logger.info("Backup created at: %s", backup_path)

    # Read the entire file content first to preserve formatting
    content = file_path.read_text(encoding="utf-8")

    # Extract scripts section while preserving formatting
    content, scripts_section = extract_scripts_section(content)

    # Load and process the TOML
    pyproject = tomlkit.loads(content)
    poetry_section = pyproject.get("tool", {}).get("poetry", {})
    if not poetry_section:
        msg = "No [tool.poetry] section found in pyproject.toml"
        raise ValueError(msg)

    # Create new document
    new_pyproject = tomlkit.document()

    new_pyproject["build-system"] = {
        "requires": ["poetry-core>=2.0"],
        "build-backend": "poetry.core.masonry.api",
    }

    # Project section
    project = create_basic_project(poetry_section)
    handle_dependencies(poetry_section, project)
    new_pyproject["project"] = project

    # Preserve Poetry-specific configuration
    tool_poetry = tomlkit.table()
    for field in POETRY_SPECIFIC_FIELDS - {"scripts"}:
        if field in poetry_section:
            tool_poetry[field] = poetry_section[field]

    if tool_poetry:
        new_pyproject["tool"] = {"poetry": tool_poetry}

    # Write the new configuration
    file_path.write_text(
        tomlkit.dumps(new_pyproject)
        + ("\n[project.scripts]" + scripts_section if scripts_section else ""),
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="update Poetry pyproject.toml files to 2.0 format")
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
                logger.info("Found pyproject.toml file: %s", args.file)

                if not args.confirm:
                    logger.info("Run with --confirm to perform the conversion.")
                    return 0

                logger.info("Performing conversion...")
                convert_pyproject(args.file)
                logger.info("Conversion complete!")
                return 0

            except (FileNotFoundError, ValueError) as e:
                logger.error("An error occurred: %s", str(e))
                return 1

        # Handle directory scanning
        pyproject_files = find_pyproject_files(args.path)

        if not pyproject_files:
            logger.error("No pyproject.toml files found under %s", args.path)
            return 1

        for file in pyproject_files:
            rel_path = file.relative_to(args.path)
            logger.info("Found pyproject.toml file: %s", rel_path)

        if not args.confirm:
            logger.info("Run with --confirm to perform the conversion.")
            return 0

        logger.info("Performing conversion...")
        for file in pyproject_files:
            rel_path = file.relative_to(args.path)
            logger.info("Converting %s.", rel_path)
            convert_pyproject(file)

        logger.info("Conversion complete!")
        return 0

    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
