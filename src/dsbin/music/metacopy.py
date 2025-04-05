#!/usr/bin/env python3

"""Copy audio metadata from a known file to a new file."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from polykit.core import polykit_setup
from polykit.log import Logician

polykit_setup()

logger = Logician.get_logger("metacopy")


def copy_metadata(file: Path, metadata_source: Path | None, rename_flag: bool) -> None:
    """Copy metadata from a known file to a new file."""
    # Determine the source for metadata
    actual_metadata_source = metadata_source or file

    if not actual_metadata_source.exists():
        logger.warning("File not found in source location: %s", actual_metadata_source.name)
        return

    # Create a temporary file
    temp_file = file.with_name(f"temp_{file.name}")

    # Copy metadata to temporary file
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(actual_metadata_source),
            "-i",
            str(file),
            "-map",
            "1:a",
            "-map",
            "0:v?",
            "-c",
            "copy",
            "-map_metadata",
            "0",
            str(temp_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        logger.info("Metadata copied: %s", file.name)
    else:
        logger.error("Error copying metadata for '%s': %s", file.name, result.stderr)
        return

    target_file = file

    if rename_flag:
        track = get_metadata_value(actual_metadata_source, "track")
        title = get_metadata_value(actual_metadata_source, "TITLE")

        if track and title:
            track = f"{int(track):02d}"
            new_name = f"{track} - {title}{file.suffix}"
            target_file = file.with_name(new_name)
            temp_file.rename(target_file)
            logger.info("Renamed %s to %s.", file.name, target_file.name)
        else:
            logger.warning("Keeping original name as no metadata was found: %s", file.name)
            temp_file.rename(file)
    else:
        temp_file.rename(file)


def get_metadata_value(file: Path, tag: str) -> str:
    """Get a specific metadata value from a file."""
    result = subprocess.run(
        [
            "ffprobe",
            "-hide_banner",
            "-show_entries",
            f"format_tags={tag}",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Copy audio metadata from a known file to a new file"
    )
    parser.add_argument("--rename", action="store_true", help="Rename files based on metadata")
    parser.add_argument("--source", required=True, help="Metadata source file or directory")
    parser.add_argument("files", nargs="+", help="Input files or wildcards")
    return parser.parse_args()


def main() -> None:
    """Identify the files and copy the metadata."""
    args = parse_arguments()

    metadata_source = Path(args.source)
    if not metadata_source.exists():
        logger.error("Source location not found: %s", metadata_source.name)
        sys.exit(1)

    for file in args.files:
        file_path = Path(file)
        source = metadata_source / file_path.name if metadata_source.is_dir() else metadata_source
        copy_metadata(file_path, source, args.rename)


if __name__ == "__main__":
    main()
