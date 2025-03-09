#!/usr/bin/env python3

"""
Alfred Script Filter that searches for Python files in specified directories. It allows for
exclusion of certain directories and displays relative paths in the subtext field. The directories
and extensions are defined at the start as BASE_DIRS, FILE_EXTENSIONS, and EXCLUDED_DIRS.

This Script Filter requires Alfred 5.5 or higher, and should be used with 'Alfred filters results'
enabled in the workflow with one of the 'Word matching' match modes. Results will be cached and
refreshed at RELOAD_INTERVAL_MINUTES unless changes are detected. The 'loosereload' option attempts
to load the cache first and refresh in the background to minimize the delay in showing results.

Workflow metadata can be whatever you want, but these are my recommendations:
- Keyword:                  py (with space, argument required)
- Placeholder Title:        Search for Python Files
- Placeholder Subtext:      Search for Python files in your development directories
- "Please Wait" Subtext:    Searching for Python files…

Alfred Script Filter reference: https://www.alfredapp.com/help/workflows/inputs/script-filter/
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

# Get base directory from environment variable, or use default
BASE_DIR_ARG = os.getenv("BASE_DIR", "~/Developer")
BASE_DIR = os.path.expanduser(BASE_DIR_ARG)

# Get additional file extensions from environment variable
ADDITIONAL_EXTS = os.getenv("ADDITIONAL_EXTS", "")
FILE_EXTENSIONS = [".py"] + [ext.strip() for ext in ADDITIONAL_EXTS.split(",") if ext.strip()]

EXCLUDED_DIRS = ["venv", "node_modules", "__pycache__"]

RELOAD_INTERVAL_MINUTES = 120


def get_file_metadata(file_path: str, base_dir: str) -> tuple[str, str, float]:
    """
    Get the desired title, subtitle, and modification time for a Python file.

    Args:
        file_path: The path to the Python file.
        base_dir: The base directory being searched.

    Returns:
        The title, subtitle, and modification time for the file.
    """
    title = os.path.basename(file_path)
    relative_path = os.path.relpath(file_path, base_dir)
    subtitle = os.path.dirname(relative_path)
    time = os.path.getmtime(file_path)

    return title, subtitle, time


def find_files_in_directory(base_dir: str) -> list[dict[str, Any]]:
    """
    Find Python files in a single directory.

    Args:
        base_dir: The base directory to search in.

    Returns:
        A list of dictionaries containing the metadata for each file in Alfred's JSON format.
    """
    results = []

    for root, dirs, files in os.walk(base_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for name in files:
            if any(name.endswith(ext) for ext in FILE_EXTENSIONS):
                file_path = os.path.join(root, name)
                results.append(process_file_for_alfred(file_path, base_dir))

    return results


def process_file_for_alfred(file_path: str, base_dir: str) -> dict[str, Any]:
    """
    Process a single file and return its metadata in Alfred's JSON format.

    Args:
        file_path: The path to the file to process.
        base_dir: The base directory being searched.

    Returns:
        A dictionary containing the metadata for the file in Alfred's JSON format.
    """
    title, subtitle, time = get_file_metadata(file_path, base_dir)
    return {
        "uid": file_path,
        "type": "file",
        "title": title,
        "subtitle": subtitle,
        "arg": file_path,
        "autocomplete": title,
        "icon": {"type": "fileicon", "path": file_path},
        "time": time,
    }


result = find_files_in_directory(BASE_DIR)
json_output = json.dumps({
    "cache": {
        "seconds": RELOAD_INTERVAL_MINUTES * 60,
        "loosereload": "true",
    },
    "items": result,
    "skipknowledge": "true",
})
sys.stdout.write(json_output)
