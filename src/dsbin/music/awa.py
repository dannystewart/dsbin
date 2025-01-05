"""Convert AIFF to WAV or WAV to AIFF, with optional Logic metadata.

This script converts AIFF files to WAV using ffmpeg, or vice versa. Optionally, Logic Pro metadata
can be added to the AIFF files for cases when the original AIFF files may have had Logic metadata
that was removed when converted to WAV.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Literal

from dsutil import configure_traceback
from dsutil.files import list_files
from dsutil.macos import get_timestamps, set_timestamps
from dsutil.media import ffmpeg_audio
from dsutil.text import print_colored

configure_traceback()

AudioFormat = Literal["wav", "aif"]


def convert_audio(
    file_path: str, target_format: AudioFormat, version: str | None = None, recursive: bool = False
) -> None:
    """Convert audio files between WAV and AIFF formats.

    Args:
        file_path: File or directory of audio files to convert.
        target_format: The target format to convert to ("wav" or "aif").
        version: Logic Pro version number (only for WAV to AIFF conversion).
        recursive: Search for files recursively.
    """
    source_format = "aif" if target_format == "wav" else "wav"
    source_extensions = ["aif", "aiff"] if source_format == "aif" else ["wav"]

    if not (os.path.isdir(file_path) or os.path.isfile(file_path)):
        print(f"The path specified does not exist: {file_path}")
        return

    if os.path.isfile(file_path):
        source_files = [file_path]
    else:
        source_files = list_files(file_path, extensions=source_extensions, recursive=recursive)

    metadata_options = None
    if version and target_format == "aif":
        metadata_options = ["metadata", f"comment=Creator: Logic Pro X {version}"]

    for source_file in source_files:
        target_file = f"{os.path.splitext(source_file)[0]}.{target_format}"

        if not os.path.exists(target_file):
            ffmpeg_audio(
                input_files=source_file,
                output_format=target_format,
                additional_args=metadata_options,
                show_output=True,
            )
            ctime, mtime = get_timestamps(source_file)
            set_timestamps(target_file, ctime=ctime, mtime=mtime)
        else:
            print(f"Skipping {source_file} ({target_format.upper()} version already exists).")


def aif2wav() -> None:
    """Convert AIFF files to WAV format."""
    sys.argv.extend(["--to", "wav"])
    main()


def wav2aif() -> None:
    """Convert WAV files to AIFF format."""
    sys.argv.extend(["--to", "aif"])
    main()


def parse_args() -> argparse.Namespace:
    """Parse arguments passed in from the command line."""
    parser = argparse.ArgumentParser(description="Convert between WAV and AIFF audio formats.")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the file, wildcard, or directory containing audio files to convert.",
    )
    parser.add_argument(
        "--to", choices=["wav", "aif"], required=True, help="Target format to convert to."
    )
    parser.add_argument("--logic", "-l", type=str, help="add Logic version metadata to AIFF files")
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Search for files recursively."
    )
    return parser.parse_args()


def main() -> None:
    """Convert between WAV and AIFF formats."""
    args = parse_args()

    if args.logic and not re.match(r"^(10|11)\.\d+(?:\.\d+)?$", args.logic):
        print_colored("Error: Version number must use format 10.x, 10.x.x, 11.x, or 11.x.x", "red")
        sys.exit(1)

    if args.logic and args.to != "aif":
        print_colored(
            "Warning: Logic version is only applicable when converting to AIFF.", "yellow"
        )

    convert_audio(args.path, args.to, version=args.logic, recursive=args.recursive)


if __name__ == "__main__":
    main()
