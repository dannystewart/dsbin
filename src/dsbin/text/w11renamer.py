#!/usr/bin/env python3

"""Generates non-stupid filenames for Windows 11 ISO files from stupid ones.

Microsoft names files with a stupid incomprehensible meaningless name like
`22631.3007.240102-1451.23H2_NI_RELEASE_SVC_PROD1_CLIENTPRO_OEMRET_X64FRE_EN-US.ISO`, so
this turns that into `Win11_22631.3007_Pro_x64.iso` because it's not stupid.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from dsbase.log import LocalLogger
from dsbase.text import color
from dsbase.util import dsbase_setup

dsbase_setup()

logger = LocalLogger().get_logger(simple=True, color=False)


def parse_arguments() -> argparse.Namespace | None:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Turns stupid Windows 11 ISO names into non-stupid ones."
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="Windows 11 ISO filename or string to process",
    )
    parser.add_argument(
        "--rename",
        action="store_true",
        help="rename the file if it exists",
    )
    args = parser.parse_args()

    if not args.filename:
        parser.print_help()
        return

    return args


def handle_naming(input_name: str | Path, rename: bool = False) -> None:
    """Handle generating the new name and optionally performing the rename."""
    # Convert to string if it's a Path
    original_name = input_name.name if isinstance(input_name, Path) else input_name

    # Get the new name and add the .iso extension back if the original had it
    new_name = destupify_filename(original_name)
    if original_name.upper().endswith(".ISO"):
        new_name = f"{new_name}.iso"

    print()
    if rename and isinstance(input_name, Path):
        try:
            # Rename the file
            input_name.rename(input_name.parent / new_name)
            logger.info(
                "\nRenamed: \n%s → %s", color(original_name, "yellow"), color(new_name, "green")
            )
        except OSError as e:
            logger.error("Could not rename file: %s", str(e))
            sys.exit(1)
    else:
        if rename:
            logger.debug("NOTE: Cannot rename when processing input as text only.")
        logger.info("New filename: \n%s", color(new_name, "green"))


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
    if not args:
        return

    input_path = Path(args.filename)

    # If it's a real file, process it as such, otherwise treat as string
    if input_path.exists():
        handle_naming(input_path, args.rename)
    else:
        handle_naming(args.filename, False)


if __name__ == "__main__":
    main()
