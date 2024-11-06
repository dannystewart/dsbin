#!/usr/bin/env python3

"""
Lists executable files and their descriptions based on comments.

This script is designed to list executable files in a specified bin directory (e.g. for utility
scripts) and prints their description based on comments at the top of the file. For Python scripts,
by default it searches for a docstring block (like the one you're reading right now) and returns the
first line. Otherwise, it looks for a comment line at the top. It also identifies files that are
missing descriptions, because public shaming is highly effective.

You can customize the bin directory, the number of lines to search before giving up on finding a
description, and a list of files to exclude from the search using the variables at the top.
"""

from __future__ import annotations

import argparse
import os
import re

from dsutil.text import color, print_colored

# Define script directories
BIN_DIR = os.path.join(os.path.expanduser("~"), ".local/bin")
RETIRED_DIR = os.path.join(BIN_DIR, "retired")
INCLUDE_DIRS = [BIN_DIR]
EXCLUDE_DIRS = [RETIRED_DIR]

# Define colors for script types
SCRIPT_COLORS = {
    "Python": {
        "header": "cyan",
        "name": "green",
    },
    "Bash": {
        "header": "blue",
        "name": "yellow",
    },
    "default": {
        "header": "cyan",
        "name": "white",
    },
}

# Define max number of lines to search for description at start of file
MAX_LINES_TO_SEARCH = 10

# Define column widths
COLUMN_BUFFER = 2
SCRIPT_WIDTH = 16
DESC_WIDTH = 50

# Define exclusions from the list
EXCLUDE_SCRIPTS = {
    "displayplacer",
    "evdownloader",
    "evremixes",
    "git-snap",
    "lunar",
    "markdown-it",
    "normalizer",
    "poetry",
    "pybounce.sh",
    "pygmentize",
    "short",
    "virtualenv",
}


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="List executables and their descriptions.")
    parser.add_argument("--excluded", action="store_true", help="Show only excluded scripts.")
    parser.add_argument("search_term", nargs="?", default="", help="Search term to filter results.")
    return parser.parse_args()


def get_executable_files(
    included_dirs: list[str], excluded_dirs: list[str], show_excluded: bool
) -> list[str]:
    """
    Return a list of executable files from included directories or excluded directories, filtering
    out files specified in the `EXCLUDE_SCRIPTS` list unless the `show_excluded`flag is enabled.

    Args:
        included_dirs: List of directories to include by default.
        excluded_dirs: List of directories to consider when `show_excluded` is True.
        show_excluded: If True, return files from `excluded_dirs`, ignoring `EXCLUDE_SCRIPTS` list.

    Returns:
        A list of executable file paths.
    """
    target_dirs = excluded_dirs if show_excluded else included_dirs
    exec_files = []

    for dir_path in target_dirs:
        if os.path.isdir(dir_path):
            files = sorted(
                f
                for f in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, f))
                and os.access(os.path.join(dir_path, f), os.X_OK)
            )
            for file in files:
                filepath = os.path.join(dir_path, file)
                if not show_excluded and file not in EXCLUDE_SCRIPTS or show_excluded:
                    exec_files.append(filepath)

    return exec_files


def find_description(file_path: str) -> tuple[str, str | None, str | None]:
    """
    Given a file path, find the description of the script based on comments or docstrings, and
    determine if it is a Python script based on the shebang line.

    Args:
        file_path: The file path.

    Returns:
        A tuple containing the type of script, the description, and the type of description.
    """
    with open(file_path, errors="ignore", encoding="utf-8") as f:
        lines = f.readlines()[:MAX_LINES_TO_SEARCH]

    description = None
    description_type = None
    script_shebang = lines[0].strip() if lines else ""

    is_python_script = script_shebang.startswith("#!") and "python" in script_shebang
    script_type = "Python" if is_python_script else "Bash"

    if is_python_script:
        description = find_python_description(lines)
        description_type = "python"
    else:
        description = find_bash_description(lines)
        description_type = "bash"

    return script_type, description, description_type


def find_python_description(lines: list[str]) -> str | None:
    """Find description in Python files, checking for docstrings and comments."""
    in_docstring = False
    docstring_content = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('"""'):
            if in_docstring:
                # End of multi-line docstring
                in_docstring = False
                if docstring_content:
                    return docstring_content[0]  # Return first non-empty line
            else:
                # Start of docstring
                in_docstring = True
                # Check for single-line docstring
                if stripped.endswith('"""') and len(stripped) > 6:
                    return stripped.replace('"""', "").strip()
        elif in_docstring:
            if stripped:
                docstring_content.append(stripped)
        elif stripped.startswith("#") and not stripped.startswith("#!"):
            comment = stripped[1:].strip()
            if comment and not comment.lower().startswith(("import ", "from ", "coding:", "-*-")):
                return comment

    # If we've collected docstring content but never found the end, return the first line
    return docstring_content[0] if docstring_content else None


def find_bash_description(lines: list[str]) -> str | None:
    """Find description in Bash files, checking for comments."""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("#!"):
            if comment := stripped[1:].strip():
                return comment
    return None


def collect_descriptions(
    file_paths: list[str],
) -> tuple[list[tuple[str, str, str, str | None]], list[tuple[str, str]]]:
    """
    Collect descriptions and types from a list of files.

    Args:
        file_paths: The list of file paths.

    Returns:
        A tuple containing a list of files with descriptions, types, and a list of files without
            descriptions.
    """
    files_with_description = []
    files_without_description = []

    for file_path in file_paths:
        filename = os.path.basename(file_path)
        script_type, description, description_type = find_description(file_path)

        if description and not is_likely_missing_description(description):
            files_with_description.append((filename, script_type, description, description_type))
        else:
            files_without_description.append((filename, script_type))

    return files_with_description, files_without_description


def find_docstring_description(lines: list[str]) -> str | None:
    """
    Given a list of lines, find the description of the script based on the docstring. Assumes the
    description is given in the initial docstring.

    Args:
        lines: The list of lines in the file.

    Returns:
        The description of the script, or None if no description is found.
    """
    in_docstring = False
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('"""') and stripped_line.endswith('"""'):
            # Single line docstring
            return stripped_line.strip('"""').strip()  # noqa: B005
        if stripped_line.startswith('"""'):
            if not in_docstring:
                in_docstring = True
            else:
                break
        elif in_docstring:
            if description := stripped_line:
                return description
    return None


def is_likely_missing_description(description: str | None) -> bool:
    """
    Check if the description is likely missing based on common import patterns.

    Args:
        description: The detected description.

    Returns:
        True if the description is likely missing, False otherwise.
    """
    if description is None:
        return True

    import_patterns = [r"^from\s+\w+(\.\w+)*\s+import", r"^import\s+\w+(\s*,\s*\w+)*$"]

    return any(re.match(pattern, description) for pattern in import_patterns)


def find_comment_description(lines: list[str]) -> str | None:
    """
    Given a list of lines, find the description of the script based on comments. Assumes the
    description is given in the initial comment block.

    Args:
        lines: The list of lines in the file.

    Returns:
        The description of the script, or None if no description is found.
    """
    description_started = False
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("#!"):
            continue
        if "shellcheck" in stripped_line or "coding: " in stripped_line:
            continue
        if stripped_line.startswith(("#", "//")):
            if len(stripped_line.lstrip("#/ ").strip()) > 0:
                return stripped_line.lstrip("#/ ").strip()
            if description_started:
                break
        elif description_started:
            break
    return None


def calculate_script_width(
    files_with_desc: list[tuple[str, str, str, str | None]],
    files_without_desc: list[tuple[str, str]],
) -> int:
    """
    Calculate the maximum script name width based on the current list of files.

    Args:
        files_with_desc: A list of tuples containing the file name and other properties for files
            with descriptions.
        files_without_desc: A list of tuples containing the file name and script type for files
            without descriptions.

    Returns:
        The width to use for displaying script names.
    """
    max_filename_length_with_desc = max(
        (
            len(filename[:-3] if script_type == "Bash" and filename.endswith(".sh") else filename)
            for filename, script_type, _, _ in files_with_desc
        ),
        default=0,
    )
    max_filename_length_without_desc = max(
        (
            len(filename[:-3] if script_type == "Bash" and filename.endswith(".sh") else filename)
            for filename, script_type in files_without_desc
        ),
        default=0,
    )
    return max(max_filename_length_with_desc, max_filename_length_without_desc) + COLUMN_BUFFER


def display_descriptions(
    files_with_desc: list[tuple[str, str, str, str | None]],
    files_without_desc: list[tuple[str, str]],
    search_term: str = "",
) -> None:
    """
    Display the descriptions and types of executable files and list those without descriptions.

    Args:
        files_with_desc: A list of tuples containing the file name, script type, description, and
            description type.
        files_without_desc: A list of tuples containing file names and script types without
            descriptions.
        search_term: The search term used to filter results, if any.
    """
    if not files_with_desc and not files_without_desc:
        if search_term:
            print_colored(f"No results found for search term '{search_term}'.", "yellow")
        else:
            print_colored("No executable files found.", "yellow")
        return

    if search_term:
        print_colored(f"Showing only results containing '{search_term}':", "cyan")
        print()

    script_width = calculate_script_width(files_with_desc, files_without_desc)
    _display_with_description(files_with_desc, script_width)
    _display_without_description(files_without_desc, script_width)


def _display_with_description(files: list[tuple[str, str, str, str | None]], width: int) -> None:
    """Display files with descriptions, grouped by script type."""
    grouped_files: dict[str, list[tuple[str, str, str | None]]] = {}
    for filename, script_type, description, description_type in files:
        if script_type not in grouped_files:
            grouped_files[script_type] = []
        grouped_files[script_type].append((filename, description, description_type))

    for script_type, file_group in grouped_files.items():
        print_header(script_type, width)
        for filename, description, description_type in file_group:
            print_description(filename, description, description_type, script_type, width)


def _display_without_description(files: list[tuple[str, str]], width: int) -> None:
    """Display files without descriptions, grouped by script type."""
    if not files:
        return

    print()
    print_colored("Files without descriptions:", "red")
    grouped_no_desc: dict[str, list[str]] = {}
    for filename, script_type in files:
        if script_type not in grouped_no_desc:
            grouped_no_desc[script_type] = []
        grouped_no_desc[script_type].append(filename)

    for script_type, filenames in grouped_no_desc.items():
        print_header(script_type, width)
        for filename in filenames:
            print_colored(f"{filename:<{width}}", "white")


def filter_results(
    files_with_desc: list[tuple[str, str, str, str | None]],
    files_without_desc: list[tuple[str, str]],
    search_term: str,
) -> tuple[list[tuple[str, str, str, str | None]], list[tuple[str, str]]]:
    """
    Filter the results based on the search term.

    Args:
        files_with_desc: A list of tuples containing the file name, script type, description, and
            description type.
        files_without_desc: A list of tuples containing file names and script types without
            descriptions.
        search_term: The term to search for in filenames and descriptions.

    Returns:
        A tuple containing filtered lists of files with and without descriptions.
    """
    search_term = search_term.lower()

    filtered_with_desc = [
        (filename, script_type, description, desc_type)
        for filename, script_type, description, desc_type in files_with_desc
        if search_term in filename.lower() or (description and search_term in description.lower())
    ]

    filtered_without_desc = [
        (filename, script_type)
        for filename, script_type in files_without_desc
        if search_term in filename.lower()
    ]

    return filtered_with_desc, filtered_without_desc


def print_header(script_type: str, script_width: int) -> None:
    """
    Print a header for a script or program description.

    Args:
        script_type: The type of script or program ('Python' or 'Bash').
        script_width: The width to use for displaying script names.
    """
    head_color = SCRIPT_COLORS.get(script_type, SCRIPT_COLORS["default"])["header"]
    head_title = f"{script_type} Scripts"
    desc_title = "Description"
    print()
    print_colored(
        f"{head_title:<{script_width}} {desc_title:<{DESC_WIDTH}}",
        head_color,
        attrs=["bold", "underline"],
    )


def print_description(
    filename: str,
    description: str,
    description_type: str | None,
    script_type: str,
    script_width: int,
) -> None:
    """
    Print a script or program name and description in a given color. Optionally trims '.sh' extension.

    Args:
        filename: The name of the script or program.
        description: The description of the script or program.
        description_type: Type of the description ('docstring' or 'comment').
        script_type: The type of the script ('Python' or 'Bash').
        script_width: The width to use for displaying script names.
    """
    if script_type == "Bash" and filename.endswith(".sh"):
        filename = filename[:-3]

    name_color = SCRIPT_COLORS.get(script_type, SCRIPT_COLORS["default"])["name"]
    description_color = "white" if description_type == "docstring" else "light_grey"
    print(color(f"{filename:<{script_width}} ", name_color) + color(description, description_color))


def main() -> None:
    """Extract descriptions, filter based on search term, and display them."""
    args = parse_arguments()
    exec_files = get_executable_files(INCLUDE_DIRS, EXCLUDE_DIRS, args.excluded)
    files_with_description, files_without_description = collect_descriptions(exec_files)

    if args.search_term:
        files_with_description, files_without_description = filter_results(
            files_with_description, files_without_description, args.search_term
        )

    display_descriptions(files_with_description, files_without_description, args.search_term)


if __name__ == "__main__":
    main()
