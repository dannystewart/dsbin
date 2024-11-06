#!/usr/bin/env python3

"""Converts files to MP3."""

from __future__ import annotations

import argparse
import os
import sys

from termcolor import colored

from dsutil.files import list_files
from dsutil.media import ffmpeg_audio

allowed_extensions = [".aiff", ".aif", ".wav", ".m4a", ".flac"]


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert audio files to MP3")
    parser.add_argument(
        "path",
        nargs="?",
        default=os.getcwd(),
        help="File or directory of files to convert",
    )
    return parser.parse_args()


def main():
    """Convert a file to MP3."""
    args = parse_arguments()
    path = args.path

    if os.path.isdir(path):
        files_to_convert = list_files(
            directory=path,
            extensions=allowed_extensions,
        )
    elif os.path.isfile(path) and os.path.splitext(path)[1].lower() in allowed_extensions:
        files_to_convert = [path]
    else:
        print(colored("Provided path is neither a supported file nor a directory.", "red"))
        sys.exit(1)

    if not files_to_convert:
        print(colored("No files needing conversion.", "green"))
        sys.exit(0)

    ffmpeg_audio(
        input_files=files_to_convert, output_format="mp3", audio_bitrate="320k", show_output=True
    )


if __name__ == "__main__":
    main()
