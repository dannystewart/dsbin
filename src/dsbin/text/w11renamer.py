#!/usr/bin/env python3

"""
Generates non-stupid filenames for Windows 11 ISO files from stupid ones.

Microsoft names files with a stupid incomprehensible meaningless name like
`22631.3007.240102-1451.23H2_NI_RELEASE_SVC_PROD1_CLIENTPRO_OEMRET_X64FRE_EN-US.ISO`, so
this turns that into `Win11_22631.3007_Pro_x64.iso` because it's not stupid.

You can enter it with or without `.iso`. It'll output without it for easier copying.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from dsutil import configure_traceback
from dsutil.log import LocalLogger

configure_traceback()

logger = LocalLogger.setup_logger(message_only=True)


def handle_naming(input_path: Path, rename: bool) -> None:
    """Handle generating the new name and optionally performing the rename."""
    # Get the new name and add the .iso extension back if the original had it
    new_name = destupify_filename(input_path.name)
    if input_path.name.upper().endswith(".ISO"):
        new_name = f"{new_name}.iso"

    print()
    if rename:
        try:  # Rename the file
            input_path.rename(input_path.parent / new_name)
            logger.info("Renamed: %s → %s", input_path.name, new_name)
        except OSError as e:
            logger.error("Could not rename file: %s", str(e))
            sys.exit(1)
    else:  # Strip .iso for output if we're just displaying
        if new_name.lower().endswith(".iso"):
            new_name = new_name[:-4]
        logger.debug("NOTE: Name is only displayed. Use `--rename` to actually rename.")
        logger.info("New filename: %s", new_name)


def destupify_filename(filename: str) -> str:
    """Turn a stupid Windows 11 ISO filename into a non-stupid one."""
    if filename.upper().endswith(".ISO"):
        filename = filename[:-4]

    segments = re.split(r"[._-]", filename)

    build = segments[0]
    revision = segments[1]

    arch = None
    for segment in segments:
        if "X64FRE" in segment.upper():
            arch = "x64"
            break
        if "ARM64FRE" in segment.upper() or "A64FRE" in segment.upper():
            arch = "ARM64"
            break

    return f"Win11_{build}.{revision}_Pro_{arch}"


def parse_args() -> argparse.ArgumentParser:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Turn stupid Windows 11 ISO names into non-stupid ones"
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="Windows 11 ISO filename to process",
    )
    parser.add_argument(
        "--rename",
        action="store_true",
        help="rename the file instead of just showing the new name",
    )
    return parser


def main() -> None:
    """Main function."""
    parser = parse_args()
    args = parser.parse_args()

    if not args.filename:
        parser.print_help()
        return

    input_path = Path(args.filename)
    if not input_path.exists():
        logger.error("File not found: %s", input_path)
        sys.exit(1)

    handle_naming(input_path, args.rename)


if __name__ == "__main__":
    main()
