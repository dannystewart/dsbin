#!/usr/bin/env python3

"""Use ffmpeg to trim a video file without re-encoding."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from polykit import polykit_setup

polykit_setup()


def convert_to_hhmmss(time_str: str) -> str:
    """Convert MM:SS or HH:MM:SS format to HH:MM:SS.

    Raises:
        ValueError: If the time format is invalid.
    """
    if time_str == "0":  # '0' should begin at the beginning
        return "00:00:00"

    parts = time_str.split(":")
    if len(parts) == 1:  # SS format
        return f"00:00:{time_str}"
    if len(parts) == 2:  # MM:SS format
        return f"00:{time_str}"
    if len(parts) == 3:  # HH:MM:SS format
        return time_str
    msg = "Invalid time format. Must be MM:SS or HH:MM:SS."
    raise ValueError(msg)


def determine_output_file(input_file: str, output_file: str) -> tuple[str, str, str, list[str]]:
    """Determine the correct output file extension and codec."""
    input_ext = Path(input_file).suffix.lower()
    output_ext = Path(output_file).suffix.lower()

    if not output_ext:
        output_ext = input_ext
        output_file += input_ext

    if (output_ext == ".mp4" and input_ext == ".mp4") or output_ext != ".mp4":
        video_codec = "copy"
        audio_codec = "copy"
        metadata_flag = []
    else:
        video_codec = "libx264"
        audio_codec = "aac"
        metadata_flag = ["-map_metadata", "-1"]

    return output_file, video_codec, audio_codec, metadata_flag


def main() -> None:
    """Trim the input video file."""
    parser = argparse.ArgumentParser(description="Trim a video file without re-encoding.")
    parser.add_argument("input_file", type=str, help="Input video file.")
    args = parser.parse_args()

    try:
        start_time = input("Enter the start time (as HH:MM:SS, MM:SS, SS, or '0' for 00:00:00): ")
        end_time = input("Enter the end time (as HH:MM:SS, MM:SS, or SS): ")
        output_file = input(
            "Enter the output filename either without extension or with .mp4 extension: "
        )

        start_time = convert_to_hhmmss(start_time)
        end_time = convert_to_hhmmss(end_time)

        output_file, video_codec, audio_codec, metadata_flag = determine_output_file(
            args.input_file, output_file
        )

        ffmpeg_command = [
            "ffmpeg",
            "-ss",
            start_time,
            "-to",
            end_time,
            "-i",
            args.input_file,
            "-c:v",
            video_codec,
            "-c:a",
            audio_codec,
            *metadata_flag,
            output_file,
        ]

        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running ffmpeg: {e}")
    except KeyboardInterrupt:
        print("\nExiting.")
    except ValueError as e:
        print(f"ValueError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
