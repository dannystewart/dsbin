#! /usr/bin/env python3

"""
Custom yt-dlp command to ensure highest quality MP4.

This script is a shortcut to download the highest quality video available and convert it
to MP4 with H.264 and AAC audio. I wrote it because I wanted better quality than the
default MP4 option gave me but I still wanted it in H.264 for native playback, so this
script strikes the best middle ground on average.
"""

from __future__ import annotations

import re
import subprocess
import sys

from dsutil.files import delete_files, move_file
from dsutil.media import ffmpeg_video
from dsutil.progress import halo_progress
from dsutil.text import print_colored
from dsutil.tools import configure_traceback

configure_traceback()


def get_default_filename(url: str) -> str:
    """Get the output filename yt-dlp would use by default."""
    default_filename = subprocess.run(
        ["yt-dlp", "--get-filename", "-o", "%(title)s.%(ext)s", url],
        stdout=subprocess.PIPE,
        text=True,
    )
    return default_filename.stdout.strip()


def download_video(url: str) -> None:
    """Use yt-dlp to download the video at the given URL with the highest quality available."""
    subprocess.run(["yt-dlp", "-o", "%(title)s.%(ext)s", url])


def sanitize_filename(filename: str) -> str:
    """Remove annoying characters yt-dlp uses to replace colons and apostrophes."""
    filename = re.sub("：", " - ", filename)
    return re.sub("´", "'", filename)


def main() -> None:
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: ytdl <video_url>")
        sys.exit(1)

    url = sys.argv[1]

    download_video(url)
    original_filename = get_default_filename(url)
    clean_filename = sanitize_filename(original_filename)

    if original_filename == clean_filename:
        target_filename = f"temp_{clean_filename}"
    else:
        target_filename = clean_filename

    with halo_progress(filename=clean_filename):
        ffmpeg_video(
            input_files=original_filename,
            output_format="mp4",
            output_file=target_filename,
            video_codec="h264",
            audio_codec="aac",
        )

    if original_filename != target_filename:
        delete_files(original_filename)
        if move_file(target_filename, clean_filename, overwrite=True, show_output=False):
            print_colored(f"Saved {clean_filename}!", "green")


if __name__ == "__main__":
    main()
