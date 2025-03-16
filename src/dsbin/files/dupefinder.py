#!/usr/bin/env python3

"""Find duplicate files in a directory.

This script will find duplicate files in a directory and print them to the console.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dsbase import configure_traceback
from dsbase.files import find_duplicate_files_by_hash

configure_traceback()


def main() -> None:
    """Find duplicate files in a directory."""
    input_files = sys.argv[1:]
    if len(input_files) == 0:
        input_files = [f for f in Path().iterdir() if f.is_file()]

    find_duplicate_files_by_hash(input_files)


if __name__ == "__main__":
    main()
