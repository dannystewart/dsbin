#!/usr/bin/env python3

"""Lists executable files and their descriptions based on docstrings. What you're looking at now.

This script is designed to list executable files in this package and print their description from a
docstring block at the top of the file (like the one you're reading right now). It also identifies
files that are missing descriptions, because public shaming is highly effective.

The script can also update the README.md and __init__.py files with the categorized script list
when run with the --update-readme flag.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING

import tomlkit
from polykit.cli import PolyArgs
from polykit.core import polykit_setup
from polykit.formatters import color, print_color
from polykit.log import PolyLog

if TYPE_CHECKING:
    import argparse

polykit_setup()

logger = PolyLog.get_logger()

# Define column widths
COLUMN_BUFFER = 2
SCRIPT_WIDTH = 16
DESC_WIDTH = 50

# Constants for README generation
README_PATH: Path = Path("README.md")
README_TITLE: str = "# DSBin"
START_MARKER: str = "## Script List"
END_MARKER: str = "## License"

INTRO_TEXT: str = (
    "This is my personal collection of Python scripts, built up over many years of solving problems "
    "most people don't care about (or don't *know* they care about… until they discover my scripts).\n\n"
)

# Categories for organizing scripts
CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "Meta Scripts": [],
    "Development Scripts": [],
    "File Management": [],
    "Text Processing": [],
    "System Tools": [],
    "macOS-Specific Scripts": [],
    "Music Scripts": [],
    "Logic Pro Scripts": [],
    "Other Media Scripts": [],
}

# Map script modules to categories
MODULE_TO_CATEGORY: dict[str, str] = {
    "dsbin.lsbin": "Meta Scripts",
    "dsbin.dsver": "Meta Scripts",
    "dsbin.files": "File Management",
    "dsbin.workcalc": "File Management",
    "dsbin.text": "Text Processing",
    "dsbin.media": "Other Media Scripts",
    "dsbin.music": "Music Scripts",
    "dsbin.pybounce": "Music Scripts",
    "dsbin.wpmusic": "Music Scripts",
    "dsbin.mac": "macOS-Specific Scripts",
    "dsbin.logic": "Logic Pro Scripts",
    "dsbin.tools": "System Tools",
    "dsbin.updater": "System Tools",
    "dsbin.dev": "Development Scripts",
    "dsbin.pybumper": "Development Scripts",
    "dsbin.configs": "Development Scripts",
}


@dataclass
class ScriptInfo:
    """Information about a script entry point."""

    name: str
    module_path: str
    description: str
    has_description: bool


def get_script_entries() -> dict[str, str]:
    """Get script entry points from package metadata."""
    entries = entry_points(group="console_scripts")
    return {ep.name: f"{ep.module}:{ep.attr}" for ep in entries if ep.module.startswith("dsbin.")}


def get_module_or_function_docstring(module_path: str, function_name: str) -> str | None:
    """Get module or function docstring without executing the module."""
    try:
        # Convert module path to file path
        parts = module_path.split(".")
        file_path = Path(__file__).parent
        for part in parts[1:]:  # Skip 'dsbin'
            file_path /= part
        file_path = file_path.with_suffix(".py")

        with Path(file_path).open(encoding="utf-8") as f:
            module_ast = ast.parse(f.read())

        # First try to get module-level docstring
        if (module_doc := ast.get_docstring(module_ast)) is not None:
            return module_doc.split("\n")[0].strip()

        # If no module docstring, look for the function docstring
        for node in module_ast.body:
            if (
                isinstance(node, ast.FunctionDef)
                and node.name == function_name
                and (func_doc := ast.get_docstring(node)) is not None
            ):
                return func_doc.split("\n")[0].strip()

        return None
    except Exception as e:
        logger.error("Error reading docstring for %s: %s", module_path, str(e))
        return None


def is_likely_missing_description(description: str | None) -> bool:
    """Check if the description is likely missing based on common import patterns."""
    if description is None:
        return True

    import_patterns = [r"^from\s+\w+(\.\w+)*\s+import", r"^import\s+\w+(\s*,\s*\w+)*$"]

    return any(re.match(pattern, description) for pattern in import_patterns)


def get_all_script_info() -> list[ScriptInfo]:
    """Get information about all scripts in the package."""
    results = []

    for script_name, entry_point in get_script_entries().items():
        module_path, func_name = entry_point.split(":")

        if doc := get_module_or_function_docstring(module_path, func_name):
            if not is_likely_missing_description(doc):
                results.append(ScriptInfo(script_name, module_path, doc, True))
            else:
                results.append(ScriptInfo(script_name, module_path, "", False))
        else:
            results.append(ScriptInfo(script_name, module_path, "", False))

    return sorted(results, key=lambda x: x.name)


def display_script_list(scripts: list[ScriptInfo], search_term: str = "") -> None:
    """Display the descriptions and types of executable files and list those without descriptions.

    Args:
        scripts: A list of script information objects.
        search_term: The search term used to filter results, if any.
    """
    if not scripts:
        if search_term:
            logger.warning("No results found for search term '%s'.", search_term)
        else:
            logger.warning("No scripts found.")
        return

    if search_term:
        logger.info("Showing only results containing '%s':")
        print()

    # Group by description to find aliases
    grouped: dict[str, list[str]] = {}
    for script in scripts:
        if script.has_description:  # Only group scripts with descriptions
            grouped.setdefault(script.description, []).append(script.name)

    script_width = (
        max((len(", ".join(names)) for names in grouped.values()), default=SCRIPT_WIDTH)
        + COLUMN_BUFFER
    )

    print()
    print_color(
        f"{'Script Name':<{script_width}} {'Description':<{DESC_WIDTH}}",
        "cyan",
        style=["bold", "underline"],
    )

    # Sort by the shortest name in each group (typically the main command)
    sorted_items = sorted(grouped.items(), key=lambda x: min(x[1], key=len))

    # Print grouped scripts
    for desc, names in sorted_items:
        name_str = ", ".join(sorted(names, key=len))  # Sort aliases by length
        print(color(f"{name_str:<{script_width}} ", "green") + color(desc, "white"))


def filter_results(scripts: list[ScriptInfo], search_term: str) -> list[ScriptInfo]:
    """Filter the results based on the search term.

    Args:
        scripts: A list of script information objects.
        search_term: The term to search for in script names and descriptions.

    Returns:
        A filtered list of scripts matching the search term.
    """
    search_term = search_term.lower()
    return [
        script
        for script in scripts
        if search_term in script.name.lower()
        or (script.has_description and search_term in script.description.lower())
    ]


def get_categorized_scripts() -> dict[str, list[tuple[str, str]]]:
    """Parse pyproject.toml to get scripts organized by category.

    Returns:
        Dictionary mapping category names to lists of (script_name, module_path) tuples.
    """
    categories = {k: [] for k in CATEGORIES}

    try:
        with Path("pyproject.toml").open("rb") as f:
            pyproject = tomlkit.parse(f.read())

        # Get all scripts
        scripts = pyproject.get("project", {}).get("scripts", {})

        # Assign scripts to categories
        for script_name, module_path in scripts.items():
            category = None
            for prefix, cat in MODULE_TO_CATEGORY.items():
                if module_path.startswith(prefix):
                    category = cat
                    break

            if category:
                categories[category].append((str(script_name), str(module_path)))
            else:
                logger.warning(
                    "Could not determine category for script: %s (%s)", script_name, module_path
                )

        return categories

    except Exception as e:
        logger.error("Failed to parse pyproject.toml: %s", e)
        raise


def generate_readme_content(
    categories: dict[str, list[tuple[str, str]]], script_info: list[ScriptInfo]
) -> str:
    """Generate formatted README content with categorized scripts and descriptions.

    Args:
        categories: Dictionary mapping category names to lists of (script_name, module_path) tuples.
        script_info: List of script information objects.

    Returns:
        Formatted README content.
    """
    content = [""]

    # Create a lookup dictionary for script descriptions
    descriptions = {info.name: info.description for info in script_info if info.has_description}

    # Base URL for GitHub repository
    base_url = "https://github.com/dannystewart/dsbin/blob/main/src/"

    # Add each category and its scripts
    for category, scripts in categories.items():
        if not scripts:
            continue

        content.append(f"### {category}\n")

        # Group scripts by description
        desc_to_scripts: dict[str, list[tuple[str, str]]] = {}
        for script_name, module_path in sorted(scripts):
            desc = descriptions.get(script_name, "*(No description available)*")
            desc_to_scripts.setdefault(desc, []).append((script_name, module_path))

        # Add each group of scripts with their shared description
        for desc, script_entries in desc_to_scripts.items():
            if len(script_entries) > 1:
                # Combine multiple scripts with same description
                script_links = []
                for name, module_path in sorted(script_entries):
                    # Convert module path to file path
                    file_path = module_path.split(":")[0].replace(".", "/") + ".py"
                    github_url = f"{base_url}{file_path}"
                    script_links.append(f"[**{name}**]({github_url})")

                script_str = ", ".join(script_links)
                content.append(f"- {script_str}: {desc}")
            else:
                # Single script
                name, module_path = script_entries[0]
                file_path = module_path.split(":")[0].replace(".", "/") + ".py"
                github_url = f"{base_url}{file_path}"
                content.append(f"- [**{name}**]({github_url}): {desc}")

        content.append("")

    return "\n".join(content)


def update_readme(readme_path: Path, new_content: str) -> bool:
    """Update the README with new content between markers.

    Args:
        readme_path: Path to the README file.
        new_content: New content to insert.

    Returns:
        True if the README was modified, False otherwise.
    """
    if not readme_path.exists():
        logger.error("README not found: %s", readme_path)
        return False

    content = readme_path.read_text(encoding="utf-8")

    # Check for start marker
    if START_MARKER in content:
        # If both markers exist, replace content between them
        if END_MARKER in content:
            parts = content.split(START_MARKER, 1)
            before_start = parts[0]

            after_start = parts[1].split(END_MARKER, 1)
            after_end = after_start[1] if len(after_start) > 1 else ""

            new_full_content = (
                f"{before_start}{START_MARKER}\n{new_content.rstrip()}\n\n{END_MARKER}{after_end}"
            )
        else:
            # Start marker exists but no end marker
            parts = content.split(START_MARKER, 1)
            new_full_content = f"{parts[0]}{START_MARKER}\n{new_content.rstrip()}"
    # No start marker, check for end marker only
    elif END_MARKER in content:
        parts = content.split(END_MARKER, 1)
        new_full_content = f"{new_content.rstrip()}\n\n{END_MARKER}{parts[1]}"
    else:
        # If neither marker exists, replace the entire content
        new_full_content = new_content

    # Only write if content changed
    if new_full_content != content:
        logger.debug("Updating `README.md` script list.")
        readme_path.write_text(new_full_content, encoding="utf-8")
        return True

    logger.debug("`README.md` is already up to date.")
    return False


def update_init_file(content: str) -> bool:
    """Update the __init__.py file with the same content as the README.

    Args:
        content: The formatted content to write to the file.

    Returns:
        True if the file was modified, False otherwise.
    """
    init_path = Path("src/dsbin/__init__.py")

    if not init_path.exists():
        logger.error("__init__.py not found: %s", init_path)
        return False

    # Read the current content
    current_content = init_path.read_text(encoding="utf-8")

    # Format for Python docstring
    docstring_content = f'"""{INTRO_TEXT}{START_MARKER}\n\n{content}\n"""  # noqa: D415, W505\n'

    # Check if there's already a docstring
    docstring_pattern = r'^""".*?""".*?\n'

    if re.match(docstring_pattern, current_content, re.DOTALL):
        # Replace existing docstring
        new_content = re.sub(docstring_pattern, docstring_content, current_content, flags=re.DOTALL)
    else:
        # Add docstring at the beginning
        new_content = docstring_content + current_content

    # Only write if content changed
    if new_content != current_content:
        logger.debug("Updating `__init__.py` script list.")
        init_path.write_text(new_content, encoding="utf-8")
        return True

    logger.debug("`__init__.py` is already up to date.")
    return False


def update_readme_and_init() -> bool:
    """Update README.md and __init__.py with categorized script list.

    Returns:
        True if either file was updated, False otherwise.
    """
    try:
        # Get script info
        script_info = get_all_script_info()

        # Get categorized scripts from pyproject.toml
        categories = get_categorized_scripts()

        # Generate new content
        new_content = generate_readme_content(categories, script_info)

        # Update README
        readme_updated = update_readme(README_PATH, new_content)

        # Update __init__.py
        init_updated = update_init_file(new_content.replace(README_TITLE, "").strip())

        if readme_updated or init_updated:
            # Add the files to git staging if they were modified
            files_to_add = []
            if readme_updated:
                files_to_add.append("README.md")
            if init_updated:
                files_to_add.append("src/dsbin/__init__.py")

            if files_to_add:
                try:
                    subprocess.run(["git", "add", *files_to_add], check=True)
                    logger.debug("Updated files have been added to Git staging.")
                except subprocess.CalledProcessError:
                    logger.warning("Failed to add files to Git staging.")

        return readme_updated or init_updated
    except Exception as e:
        logger.error("Failed to update files: %s", str(e))
        return False


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description=__doc__)
    parser.add_argument("search_term", nargs="?", default="", help="search term to filter results")
    parser.add_argument(
        "--update-readme",
        "-u",
        action="store_true",
        help="update README.md and __init__.py script lists",
    )
    return parser.parse_args()


def main() -> int:
    """Extract descriptions, filter based on search term, and display them."""
    args = parse_arguments()

    try:
        if args.update_readme:
            if update_readme_and_init():
                logger.info("`README.md` and `__init__.py` updated successfully!")
            else:
                logger.info("`README.md` and `__init__.py` are already up to date.")
            return 0

        # Display the script list normally
        scripts = get_all_script_info()
        if args.search_term:
            scripts = filter_results(scripts, args.search_term)
        display_script_list(scripts, args.search_term)
    except Exception as e:
        logger.error("Error: %s", str(e))
        return 1

    return 0


if __name__ == "__main__":
    main()
