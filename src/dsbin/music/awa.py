"""Convert AIFF to WAV or WAV to AIFF, with optional Logic metadata.

This script converts AIFF files to WAV using ffmpeg, or vice versa. Optionally, Logic Pro metadata
can be added to the AIFF files for cases when the original AIFF files may have had Logic metadata
that was removed when converted to WAV.
"""

from __future__ import annotations

import argparse
import re
import sys
from enum import StrEnum
from pathlib import Path

from polykit.core import polykit_setup
from polykit.files import PolyFile
from polykit.formatters import print_color

from dsbin.media import MediaManager

polykit_setup()

LOGIC_VERSION_PATTERN = re.compile(r"^(10|11)\.\d+(?:\.\d+)?$")


class AudioFormat(StrEnum):
    """Audio file formats."""

    WAV = "wav"
    AIFF = "aif"


def convert_audio(
    file_path: Path,
    target_format: AudioFormat,
    version: str | None = None,
    recursive: bool = False,
) -> None:
    """Convert audio files between WAV and AIFF formats.

    Args:
        file_path: File or directory of audio files to convert.
        target_format: The target format to convert to ("wav" or "aif").
        version: Logic Pro version number (only for WAV to AIFF conversion).
        recursive: Search for files recursively.
    """
    source_format = AudioFormat.AIFF if target_format == AudioFormat.AIFF else AudioFormat.WAV
    source_extensions = ["aif", "aiff"] if source_format == AudioFormat.AIFF else ["wav"]

    if not (file_path.is_dir() or file_path.is_file()):
        print(f"The path specified does not exist: {file_path}")
        return

    files = PolyFile()
    media = MediaManager()

    if file_path.is_file():
        source_files = [file_path]
    else:
        source_files = files.list(file_path, source_extensions, recursive=recursive)

    metadata_options = None
    if version and target_format == AudioFormat.AIFF:
        metadata_options = ["metadata", f"comment=Creator: Logic Pro X {version}"]

    for source_file in source_files:
        source_file = Path(source_file)
        target_file = source_file.with_suffix(f".{target_format}")

        if not target_file.exists():
            media.ffmpeg_audio(
                input_files=source_file,
                output_format=target_format,
                additional_args=metadata_options,
                show_output=True,
            )
            ctime, mtime = files.get_timestamps(source_file)
            files.set_timestamps(target_file, ctime=ctime, mtime=mtime)
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
        help="path to file, wildcard, or directory containing files to convert",
    )
    parser.add_argument(
        "--to", choices=["wav", "aif"], required=True, help="target format to convert to"
    )
    parser.add_argument("--logic", "-l", type=str, help="add Logic version metadata to AIFF files")
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="search for files recursively"
    )
    return parser.parse_args()


def main() -> None:
    """Convert between WAV and AIFF formats."""
    args = parse_args()

    if args.logic and not LOGIC_VERSION_PATTERN.match(args.logic):
        print_color("Error: Version number must use format 10.x, 10.x.x, 11.x, or 11.x.x", "red")
        sys.exit(1)

    audio_format = AudioFormat.AIFF if args.to != "aif" else AudioFormat.WAV

    if args.logic and audio_format == AudioFormat.WAV:
        print_color("Warning: Logic version is only applicable when converting to AIFF.", "yellow")

    convert_audio(args.path, audio_format, version=args.logic, recursive=args.recursive)


if __name__ == "__main__":
    main()
