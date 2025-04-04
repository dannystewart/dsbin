#!/usr/bin/env python3

"""Converts a video file to a GIF using ffmpeg."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from polykit import polykit_setup
from polykit.cli import ArgParser

if TYPE_CHECKING:
    import argparse

polykit_setup()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(description=__doc__)
    parser.add_argument(
        "-c", "--compress", action="store_true", help="compress output file to reduce size"
    )
    parser.add_argument(
        "-f", "--fps", type=int, default=25, help="frame rate of the GIF (frames per second)"
    )
    parser.add_argument("--width", type=int, default=480, help="width of the GIF")
    parser.add_argument("input_file", type=str, help="input video file")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def main() -> None:
    """Main function."""
    args = parse_arguments()

    output_file = f"{args.input_file.rsplit('.', 1)[0]}.gif"

    if args.compress:
        ffmpeg_command = [
            "ffmpeg",
            "-i",
            args.input_file,
            "-filter_complex",
            f"[0:v] fps={args.fps},scale=w={args.width}:h=-1,split [a][b];[a] palettegen=stats_mode=diff [p];[b][p] paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle:new=1",
            output_file,
        ]
    else:
        ffmpeg_command = [
            "ffmpeg",
            "-i",
            args.input_file,
            "-filter_complex",
            f"[0:v] fps={args.fps},scale=w={args.width}:h=-1,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1",
            output_file,
        ]

    subprocess.run(ffmpeg_command, check=False)
    print(f"\nGIF conversion complete. Output file: {output_file}")


if __name__ == "__main__":
    main()
