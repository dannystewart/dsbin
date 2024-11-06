#!/usr/bin/env python3

"""
Identifies the current OS distribution.

This script is designed to identify the current OS distribution. It can be used to
determine which package manager to use for installing packages, or for other
distribution-specific tasks.
"""

from __future__ import annotations

import re
import sys

from distro.distro import main

if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    main()
