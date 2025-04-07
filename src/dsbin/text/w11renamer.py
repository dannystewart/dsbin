#!/usr/bin/env python3

"""Generates non-stupid filenames for Windows 11 ISO files from stupid ones.

Microsoft names their ISOs with a stupid incomprehensible, meaningless, and often inconsistent name
like `26100.1.240331-1435.GE_RELEASE_CLIENTPRO_OEMRET_A64FRE_EN-US.ISO`, so this turns that into
`Win11_Pro_240331_26100.1_ARM64.iso` because it's not stupid.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from polykit.cli import confirm_action
from polykit.core import polykit_setup
from polykit.formatters import color
from polykit.log import PolyLog

polykit_setup()

logger = PolyLog.get_logger(simple=True, color=False)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Turns stupid Windows 11 ISO names into non-stupid ones."
    )
    parser.add_argument("input", nargs="?", help="Windows 11 ISO filename or string to process")
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        sys.exit(0)

    return args


def destupify_filename(filename: str) -> str:
    """Turn a stupid Windows 11 ISO filename into a non-stupid one."""
    if filename.upper().endswith(".ISO"):
        filename = filename[:-4]

    build_str = _decipher_build(filename)
    date_str = _decipher_date(filename)
    arch = _decipher_arch(filename)
    edition = _decipher_edition(filename)

    if date_str:  # Prioritize date for proper sorting
        return f"Win11_{edition}_{date_str}_{build_str}_{arch}"
    return f"Win11_{edition}_{build_str}_{arch}"


def _decipher_build(filename: str) -> str:
    # First extract the date pattern so we can exclude it
    date_match = re.search(r"(\d{6})-\d{4}", filename)
    date_part = date_match.group(0) if date_match else ""

    # Remove the date part from the string for version extraction
    clean_filename = filename.replace(date_part, "") if date_part else filename

    # Now extract the build info
    build_match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", clean_filename)

    if build_match:
        major = build_match.group(1)
        minor = build_match.group(2)
        revision = build_match.group(3) or ""
    else:
        segments = re.split(r"[._-]", clean_filename)
        if len(segments) >= 2:
            major = segments[0]
            minor = segments[1]
            revision = ""

    return f"{major}.{minor}.{revision}" if revision else f"{major}.{minor}"


def _decipher_date(filename: str) -> str:
    date_match = re.search(r"(\d{6})-\d{4}", filename)
    if date_match:
        date_code = date_match.group(1)
        year = date_code[:2]
        month = date_code[2:4]
        day = date_code[4:6]

        return f"{year}{month}{day}"
    return ""


def _decipher_arch(filename: str) -> str:
    architecture = "unknown"
    if "X64FRE" in filename.upper():
        return "x64"
    if "ARM64FRE" in filename.upper() or "A64FRE" in filename.upper():
        return "ARM64"
    return architecture


def _decipher_edition(filename: str) -> str:
    edition = "Pro"
    if "CLIENTPRO" in filename.upper():
        return "Pro"
    if "CLIENTENTERPRISE" in filename.upper():
        return "Enterprise"
    if "CLIENTEDU" in filename.upper():
        return "Education"
    if "CLIENTHOME" in filename.upper():
        return "Home"
    return edition


def main() -> None:
    """Main function."""
    args = parse_arguments()

    input_name = args.input
    input_path = Path(input_name)
    is_file = input_path.is_file()

    # Get the original name (either filename or string)
    original_name = input_path.name if is_file else input_name

    # Get the new name and add the .iso extension back if the original had it
    new_name = destupify_filename(original_name)
    if original_name.upper().endswith(".ISO"):
        new_name = f"{new_name}.iso"

    print()
    logger.info("New filename: %s", color(new_name, "green"))

    # If it's a file, ask for confirmation before renaming
    if is_file and confirm_action("Do you want to rename the file?"):
        try:
            input_path.rename(input_path.parent / new_name)
            logger.info(
                "\nRenamed %s → %s", color(original_name, "yellow"), color(new_name, "green")
            )
        except OSError as e:
            logger.error("Could not rename file: %s", str(e))
            sys.exit(1)


if __name__ == "__main__":
    main()
