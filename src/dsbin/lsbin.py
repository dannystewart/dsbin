#!/usr/bin/env python3

"""Lists executable files and their descriptions based on docstrings. What you're looking at now.

This script is designed to list executable files in this package and print their description a
docstring block at the top of the file (like the one you're reading right now). Otherwise, It also
identifies files that are missing descriptions, because public shaming is highly effective.
"""

from __future__ import annotations

import argparse
import ast
import re
from importlib.metadata import entry_points
from pathlib import Path

from polykit.core import polykit_setup
from polykit.formatters import color, print_color

polykit_setup()

# Define column widths
COLUMN_BUFFER = 2
SCRIPT_WIDTH = 16
DESC_WIDTH = 50


def get_script_entries() -> dict[str, str]:
    """Get script entry points from package metadata."""
    entries = entry_points(group="console_scripts")
    return {ep.name: f"{ep.module}:{ep.attr}" for ep in entries if ep.module.startswith("dsbin.")}


def get_script_names_and_docstrings() -> list[tuple[str, str, str | None]]:
    """Get script names, their docstrings, and source."""
    results: list[tuple[str, str, str | None]] = []
    for script_name, entry_point in get_script_entries().items():
        module_path, func_name = entry_point.split(":")

        if doc := get_module_or_function_docstring(module_path, func_name):
            if not is_likely_missing_description(doc):
                results.append((script_name, doc, "docstring"))
            else:
                results.append((script_name, "", None))
        else:
            results.append((script_name, "", None))

    return sorted(results)


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
        print_color(f"Error reading docstring for {module_path}: {e}", "red")
        return None


def is_likely_missing_description(description: str | None) -> bool:
    """Check if the description is likely missing based on common import patterns."""
    if description is None:
        return True

    import_patterns = [r"^from\s+\w+(\.\w+)*\s+import", r"^import\s+\w+(\s*,\s*\w+)*$"]

    return any(re.match(pattern, description) for pattern in import_patterns)


def display_list(scripts: list[tuple[str, str, str | None]], search_term: str = "") -> None:
    """Display the descriptions and types of executable files and list those without descriptions.

    Args:
        scripts: A list of tuples containing the file name, description, and description type.
        search_term: The search term used to filter results, if any.
    """
    if not scripts:
        if search_term:
            print_color(f"No results found for search term '{search_term}'.", "yellow")
        else:
            print_color("No scripts found.", "yellow")
        return

    if search_term:
        print_color(f"Showing only results containing '{search_term}':", "cyan")
        print()

    # Group by description to find aliases
    grouped: dict[str, list[str]] = {}
    for name, desc, _ in scripts:
        if desc:  # Only group scripts with descriptions
            grouped.setdefault(desc, []).append(name)

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


def filter_results(
    scripts: list[tuple[str, str, str | None]], search_term: str
) -> list[tuple[str, str, str | None]]:
    """Filter the results based on the search term.

    Args:
        scripts: A list of tuples containing the script name, description, and description type.
        search_term: The term to search for in script names and descriptions.

    Returns:
        A filtered list of scripts matching the search term.
    """
    search_term = search_term.lower()
    return [
        (name, desc, type_)
        for name, desc, type_ in scripts
        if search_term in name.lower() or (desc and search_term in desc.lower())
    ]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="List executables and their descriptions.")
    parser.add_argument("search_term", nargs="?", default="", help="Search term to filter results.")
    return parser.parse_args()


def main() -> int:
    """Extract descriptions, filter based on search term, and display them."""
    args = parse_arguments()
    try:
        scripts = get_script_names_and_docstrings()
        if args.search_term:
            scripts = filter_results(scripts, args.search_term)
        display_list(scripts, args.search_term)
    except Exception as e:
        print_color(f"Error: {e}", "red")
        return 1
    return 0


if __name__ == "__main__":
    main()
