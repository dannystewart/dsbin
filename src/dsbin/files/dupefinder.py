#!/usr/bin/env python3

"""Find duplicate files in a directory.

This script will find duplicate files in a directory and print them to the console.
"""

from __future__ import annotations

import os
import sys

from dsutil import configure_traceback
from dsutil.files import find_duplicate_files_by_hash

configure_traceback()

if __name__ == "__main__":
    input_files = sys.argv[1:]
    if len(input_files) == 0:
        input_files = [f for f in os.listdir(".") if os.path.isfile(f)]

    find_duplicate_files_by_hash(input_files)
