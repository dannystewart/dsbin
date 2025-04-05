#!/usr/bin/env python3

"""Finds the top N file types in a directory by cumulative size.

This script analyzes a directory recursively to find the top N file types by cumulative size.
"""

from __future__ import annotations

import argparse
import operator
from collections import defaultdict
from pathlib import Path

from polykit.core import polykit_setup
from polykit.formatters import print_color as colored

polykit_setup()


def bytes_to_readable(size_in_bytes: float) -> str:
    """Convert a size in bytes to a human-readable format.

    Args:
        size_in_bytes: The size in bytes to convert.

    Returns:
        The size in a human-readable format (e.g., "4.2 MB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} YB"


def get_top_file_types(
    directory: str, top_n: int = 10, exclude: list[str] | None = None, exclude_no_ext: bool = False
) -> list[tuple[str, int]]:
    """Analyze a directory recursively to find the top N file types by cumulative size.

    Args:
        directory: The directory to analyze.
        top_n: Number of top file types to display.
        exclude: File types to exclude (e.g., [".log", ".tmp"]).
        exclude_no_ext: If True, exclude files with no extension.

    Returns:
        list: List of tuples containing the top N file types and their cumulative sizes.
    """
    if exclude is None:
        exclude = []
    # Normalize excluded extensions to start with '.'
    exclude = ["." + ext.lstrip(".") for ext in exclude]

    # Dictionary to store cumulative size of files for each extension
    file_sizes: defaultdict = defaultdict(int)

    # Traverse the directory recursively and update file_sizes
    for file_path in Path(directory).rglob("*"):
        if file_path.is_file():
            file_extension = file_path.suffix
            if not file_extension:
                if exclude_no_ext:
                    continue  # Skip files with no extension if excluded
                file_extension = "(no extension)"
            if file_extension in exclude:
                continue  # Skip excluded file types
            file_size = file_path.stat().st_size
            file_sizes[file_extension] += file_size

    return sorted(file_sizes.items(), key=operator.itemgetter(1), reverse=True)[:top_n]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Find the largest file types in a directory.")
    parser.add_argument("directory", type=str, help="The directory to analyze")
    parser.add_argument("--top", type=int, default=10, help="Number of top file types to display")
    parser.add_argument(
        "--exclude", nargs="*", default=[], help="File types to exclude (e.g., --exclude .log .tmp)"
    )
    parser.add_argument(
        "--exclude-no-ext", action="store_true", help="Exclude files with no extension"
    )

    return parser.parse_args()


def main() -> None:
    """Main function."""
    args = parse_args()

    top_file_types = get_top_file_types(args.directory, args.top, args.exclude, args.exclude_no_ext)

    print(f"Top {args.top} file types by cumulative size:")
    for file_type, size in top_file_types:
        print(f"{colored(file_type, 'cyan')}: {colored(bytes_to_readable(size), 'yellow')}")


if __name__ == "__main__":
    main()
