#!/usr/bin/env python3

"""Find duplicate files in a directory.

This script will find duplicate files in a directory and print them to the console.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dsbase.files import find_duplicate_files_by_hash
from dsbase.util import dsbase_setup

dsbase_setup()


def main() -> None:
    """Find duplicate files in a directory."""
    input_files = sys.argv[1:]
    if len(input_files) == 0:
        input_files = [str(f) for f in Path().iterdir() if f.is_file()]

    # Convert all input files to Path objects if they aren't already
    paths = [Path(f) for f in input_files]
    find_duplicate_files_by_hash(paths)


if __name__ == "__main__":
    main()
