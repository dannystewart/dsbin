#!/usr/bin/env python3

"""
Alfred Script Filter that searches for either Logic project files or Logic bounces depending on the
environment variable set when run. For Logic projects, it searches in the specified base directories
and returns them sorted by modification date. For bounces, it searches based on specific file
extensions and returns them sorted by creation date, with top-level files appearing first. The
directories and extensions are defined at the start as BASE_DIRS, LOGIC_EXT, and BOUNCE_EXTS.

This Script Filter requires Alfred 5.5 or higher, and should be used with 'Alfred filters results'
enabled in the workflow with one of the 'Word matching' match modes. Results will be cached and
refreshed at RELOAD_INTERVAL_MINUTES unless changes are detected. The 'loosereload' option attempts
to load the cache first and refresh in the background to minimize the delay in showing results.

Workflow metadata can be whatever you want, but these are my recommendations:
- Keyword:                  lp / lb (with space, argument required)
- Placeholder Title:        Search for Logic Projects / Recent Logic Bounces
- Placeholder Subtext:      Search for Logic project files / Search for recent Logic bounces
- "Please Wait" Subtext:    Searching for Logic project files… / Searching for recent Logic bounces…

Alfred Script Filter reference: https://www.alfredapp.com/help/workflows/inputs/script-filter/
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

BASE_DIRS = [
    os.path.expanduser("~/Logic"),
    os.path.expanduser("~/Music/Logic"),
]
LOGIC_EXT = ".logicx"
BOUNCE_EXTS = [".wav", ".aif", ".aiff"]
RELOAD_INTERVAL_MINUTES = 120
SEARCH_TYPE = os.getenv("SEARCH_TYPE", "bounces")


def get_file_metadata(file_path: str) -> tuple[str, str, float]:
    """
    Get the desired title, subtitle, and creation or modification time (for sorting) for a Logic
    project or bounce, to be displayed in Alfred when a corresponding search is run.

    Args:
        file_path: The path to the Logic project or bounce file.

    Returns:
        The title, subtitle, and time for the file to be sorted by.
    """
    path_parts = file_path.split(os.sep)
    logic_index = path_parts.index("Logic") + 1 if "Logic" in path_parts else 0

    if SEARCH_TYPE == "projects":
        title = _get_project_title(file_path)
        subtitle = os.sep.join(path_parts[logic_index:-1])
        time = os.path.getmtime(file_path)
    else:
        title = _get_bounce_title(file_path)
        subtitle = os.sep.join(path_parts[logic_index:])
        time = os.path.getctime(file_path)

    return title, subtitle, time


def _get_project_title(file_path: str) -> str:
    """
    Get the display title for a Logic project search result. If it's in a folder that doesn't
    contain an 'Audio Files' folder, it's in a subfolder, so prepend the name of the parent folder.
    """
    project_name = os.path.splitext(os.path.basename(file_path))[0]
    project_dir = os.path.dirname(file_path)
    parent_dir = os.path.dirname(project_dir)

    if "Audio Files" in os.listdir(parent_dir):
        parent_folder_name = os.path.basename(project_dir)
        return f"{parent_folder_name} ≫ {project_name}"
    return project_name


def _get_bounce_title(file_path: str) -> str:
    """
    Get the display title for a Logic bounce search result. If it's in a subfolder of the 'Bounces'
    folder, prepend the name of the parent folder, and rename for readability.
    """
    path_parts = file_path.split(os.sep)
    try:
        bounces_index = path_parts.index("Bounces") + 1
        title_parts = os.sep.join(path_parts[bounces_index:])
        title, _ = os.path.splitext(title_parts)
        return title.replace(os.sep, " ≫ ").replace("_Older", "Older Bounces")
    except ValueError:
        return os.path.basename(file_path)


def find_logic_files() -> list[dict[str, Any]]:
    """
    Find Logic projects or bounces in all base directories and return them sorted.

    Returns:
        A sorted list of dictionaries containing the metadata for each file in Alfred's JSON format.
    """
    results = []
    for base_dir in BASE_DIRS:
        results.extend(find_files_in_directory(base_dir))

    # Sort bounces by directory depth (top-level first), then by creation time (newest first)
    if SEARCH_TYPE == "bounces":
        results.sort(key=lambda x: (x["arg"].count(os.sep), -x["time"]))
    else:  # Sort projects by modification time (newest first)
        results.sort(key=lambda x: -x["time"])

    return results


def find_files_in_directory(base_dir: str) -> list[dict[str, Any]]:
    """
    Find Logic projects or bounces in a single directory.

    Args:
        base_dir: The base directory to search in.

    Returns:
        A list of dictionaries containing the metadata for each file in Alfred's JSON format.
    """
    results = []
    file_exts = BOUNCE_EXTS if SEARCH_TYPE == "bounces" else [LOGIC_EXT]

    for root, dirs, files in os.walk(base_dir):
        if SEARCH_TYPE == "bounces" and "Bounces" not in root.split(os.sep):
            continue
        for name in files if SEARCH_TYPE == "bounces" else dirs:
            if any(name.endswith(ext) for ext in file_exts):
                file_path = os.path.join(root, name)
                results.append(process_file_for_alfred(file_path))

    return results


def process_file_for_alfred(file_path: str) -> dict[str, Any]:
    """
    Process a single file and return its metadata in Alfred's JSON format.

    Args:
        file_path: The path to the file to process.

    Returns:
        A dictionary containing the metadata for the file in Alfred's JSON format.
    """
    title, subtitle, time = get_file_metadata(file_path)
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


result = find_logic_files()
json_output = json.dumps({
    "cache": {
        "seconds": RELOAD_INTERVAL_MINUTES * 60,
        "loosereload": "true",
    },
    "items": result,
    "skipknowledge": "true",
})
sys.stdout.write(json_output)
