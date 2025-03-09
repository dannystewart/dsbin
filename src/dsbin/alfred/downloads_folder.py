#!/usr/bin/env python3

"""
This is an Alfred Script Filter that recursively shows files and folders in your Downloads folder.
It shows results sorted by creation date (newest first) and includes the relative date in the
subtitle field.

This Script Filter requires Alfred 5.5 or higher, and should be used with 'Alfred filters results'
enabled in the workflow with one of the 'Word matching' match modes. Results will be cached and
refreshed at RELOAD_INTERVAL_MINUTES unless changes are detected. The 'loosereload' option attempts
to load the cache first and refresh in the background to minimize the delay in showing results.

Alfred Script Filter reference: https://www.alfredapp.com/help/workflows/inputs/script-filter/
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any

DOWNLOADS_DIR = os.path.expanduser("~/Downloads")


def format_timestamp(file_path: str) -> str:
    """Format the modification date of a file with relative dates for today and yesterday."""
    mod_time = os.path.getctime(file_path)
    mod_datetime = datetime.fromtimestamp(mod_time)
    now = datetime.now()

    if mod_datetime.date() == now.date():
        date_str = "Today"
    elif mod_datetime.date() == (now.date() - timedelta(days=1)):
        date_str = "Yesterday"
    else:
        date_str = mod_datetime.strftime("%b %d, %Y")
    time_str = mod_datetime.strftime("%-I:%M %p")
    return f"{date_str} at {time_str}"


def format_subtitle(file_path: str) -> str:
    """Format the subtitle with the relative path (if any) and the modification date."""
    mod_time = os.path.getctime(file_path)
    mod_datetime = datetime.fromtimestamp(mod_time)
    now = datetime.now()

    if mod_datetime.date() == now.date():
        date_str = "Today"
    elif mod_datetime.date() == (now.date() - timedelta(days=1)):
        date_str = "Yesterday"
    else:
        date_str = mod_datetime.strftime("%b %d, %Y")
    time_str = mod_datetime.strftime("%-I:%M %p")

    relative_path = os.path.relpath(file_path, DOWNLOADS_DIR)
    path_parts = os.path.split(relative_path)

    # Show the parent folder name if it's not the Downloads folder
    if path_parts[0] != ".." and os.path.dirname(relative_path) != ".":
        path_info = f"{os.path.dirname(relative_path)}/ • "
    else:
        path_info = ""

    return f"{path_info}{date_str} at {time_str}"


def find_files_in_downloads() -> list[dict[str, Any]]:
    """Find files in the Downloads folder and return them as Alfred Script Filter items."""
    results: list[dict[str, Any]] = []
    for root, dirs, files in os.walk(DOWNLOADS_DIR):
        for name in dirs + files:
            file_path = os.path.join(root, name)

            if name.startswith("."):  # Skip hidden files and folders
                continue

            results.append(
                {
                    "uid": file_path,
                    "type": "file" if os.path.isfile(file_path) else "folder",
                    "title": name,
                    "subtitle": format_timestamp(file_path),
                    "arg": file_path,
                    "icon": {
                        "type": "fileicon" if os.path.isfile(file_path) else "fileicon",
                        "path": file_path,
                    },
                    "time": os.path.getctime(file_path),
                }
            )

    results.sort(key=lambda x: x["time"], reverse=True)  # Sort by creation time (newest first)
    return results


items = find_files_in_downloads()
json_output = json.dumps(
    {
        "rerun": 0.1,
        "items": items,
    }
)
print(json_output)
