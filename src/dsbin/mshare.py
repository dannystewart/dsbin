#!/usr/bin/env python3

"""
A script for sharing music bounces in a variety of formats.

This script is designed to convert music bounces to WAV, FLAC, and MP3 files for easy
sharing with people who need or prefer different formats or for uploading to different
platforms. Also includes bit depth conversion for 24-bit files.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

import inquirer
from termcolor import colored

from dsutil import animation
from dsutil.media import find_bit_depth
from dsutil.progress import halo_progress
from dsutil.shell import handle_keyboard_interrupt

HOME_DIR = os.path.expanduser("~")
OUTPUT_PATH = os.path.join(HOME_DIR, "Downloads")


def show_format_options() -> dict[str, list[str]] | None:
    """Prompt the user for conversion options from an inquirer menu."""
    questions = [
        inquirer.Checkbox(
            "options",
            message="Select conversion options",
            choices=[
                "Copy original WAV file",
                "Convert to 16-bit WAV",
                "Convert to 16-bit FLAC",
                "Convert to 24-bit FLAC",
                "Convert to MP3",
            ],
            carousel=True,
        ),
    ]
    return inquirer.prompt(questions)


def clean_filename(input_file: str, naming_format: str) -> str:
    """
    Generate sanitized and formatted filenames for the output files. Version numbers are removed, as
    are parentheticals starting with "No" (e.g. No Vocals, No Drums).

    Notes:
    - The WAV and FLAC files are formatted with hyphens instead of spaces.
    - The MP3 file is formatted with spaces instead of hyphens.

    Args:
        input_file: The path to the input file.
        naming_format: The naming format to use (e.g. "Local", "For upload").
    """
    filename_no_ext = os.path.splitext(os.path.basename(input_file))[0]
    clean_name_pattern = re.compile(
        r"( [0-9]+([._][0-9]+){2,3}([._][0-9]+)?[a-z]{0,2}$)|(\s*\(No [^)]*\))"
    )
    clean_name = clean_name_pattern.sub("", filename_no_ext)

    if naming_format == "upload":
        clean_name = clean_name.replace(" ", "-").replace("'", "")

    return clean_name


def convert_file(
    input_file: str, output_path: str, conversion_option: dict, bit_depth: int
) -> tuple[bool, str]:
    """
    Perform an individual conversion.

    Args:
        input_file: The path to the input file.
        output_path: The path to the output directory.
        conversion_option: The details of the conversion option.
        bit_depth: The bit depth of the input file.

    Returns:
        A tuple (success, message) where success is a boolean indicating whether the conversion was
        successful, and message is a string with a success or error message.
    """
    destination_path = os.path.join(output_path, conversion_option["filename"])
    required_bit_depth = conversion_option.get("requires")
    if required_bit_depth and bit_depth not in required_bit_depth:
        return (
            False,
            f"The conversion requires {required_bit_depth} bit depth but the input is {bit_depth} bit.",
        )
    command = conversion_option["command"].format(
        input_file=input_file, destination_path=destination_path
    )

    try:
        subprocess.check_call(
            command,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)


def _get_filename(base_name: str, extension: str, suffix: str = "") -> str:
    """Generate a filename with an optional suffix."""
    return f"{base_name}{suffix}.{extension}"


def _get_conversion_options(
    input_file: str, output_path: str, output_filename: str
) -> dict[str, dict[str, str]]:
    """Construct the conversion options dictionary."""
    base_name = os.path.join(output_path, output_filename)
    wav_name = _get_filename(base_name, "wav")
    flac_name = _get_filename(base_name, "flac")
    mp3_name = _get_filename(base_name, "mp3")

    wav_16_bit_name = _get_filename(base_name, "wav", " (16-bit)")
    flac_24_bit_name = _get_filename(base_name, "flac", " (24-bit)")

    return {
        "Copy original WAV file": {
            "filename": wav_name,
            "message": "Copying",
            "completed_message": "Copied:",
            "command": f'cp "{input_file}" "{wav_name}"',
        },
        "Convert to 16-bit WAV": {
            "filename": wav_16_bit_name,
            "message": "Converting to 16-bit WAV",
            "completed_message": "Converted to 16-bit WAV:",
            "command": f'ffmpeg -i "{input_file}" -y -acodec pcm_s16le "{wav_16_bit_name}"',
        },
        "Convert to 16-bit FLAC": {
            "filename": flac_name,
            "message": "Converting to 16-bit FLAC",
            "completed_message": "Converted to 16-bit FLAC:",
            "command": f'ffmpeg -i "{input_file}" -y -acodec flac -sample_fmt s16 "{flac_name}"',
        },
        "Convert to 24-bit FLAC": {
            "filename": flac_24_bit_name,
            "message": "Converting to 24-bit FLAC",
            "completed_message": "Converted to 24-bit FLAC:",
            "command": f'ffmpeg -i "{input_file}" -y -acodec flac -sample_fmt s32 -bits_per_raw_sample 24 "{flac_24_bit_name}"',
        },
        "Convert to MP3": {
            "filename": mp3_name,
            "message": "Converting to MP3",
            "completed_message": "Converted to MP3:",
            "command": f'ffmpeg -i "{input_file}" -y -b:a 320k "{mp3_name}"',
        },
    }


def perform_conversions(
    answers: dict, input_file: str, output_path: str, output_filename: str, bit_depth: int
) -> None:
    """
    Perform the conversions selected by the user based on a dictionary of conversion options.

    Args:
        answers: The answers to the conversion options prompt.
        input_file: The path to the input file.
        output_path: The path to the output directory.
        output_filename: The clean base filename for the output file.
        bit_depth: The bit depth of the input file.
    """
    conversion_options = _get_conversion_options(input_file, output_path, output_filename)

    for option, details in conversion_options.items():
        if option in answers["options"] and isinstance(details["filename"], str):
            action, new_filename = prompt_if_file_exists(details["filename"])
            if action == "cancel":
                print(colored("Conversion canceled by user.", "yellow"))
                continue
            if action == "new_name" and new_filename is not None:
                details["filename"] = new_filename

            with halo_progress(
                filename=details["filename"],
                start_message=details["message"],
                end_message=details["completed_message"],
                fail_message="Failed",
            ) as spinner:
                success, message = convert_file(input_file, output_path, details, bit_depth)
                if not success:
                    spinner.fail(message)

    print(colored("\nAll conversions complete!", "green"))


def prompt_if_file_exists(output_file: str | None) -> tuple[str, str | None]:
    """
    Check if the output file exists with the exact same name and extension, and prompt the user to
    choose between overwriting, providing a new name, or canceling.

    Args:
        output_file: The path to the output file.

    Returns:
        A tuple (action, new_filename) where action is 'overwrite', 'new_name', or 'cancel'.
    """
    if output_file is None or not os.path.isfile(output_file):
        return "none", None
    print(f"File {output_file} already exists.")
    action = inquirer.list_input(
        "Choose an action",
        choices=["Overwrite", "Provide a new name", "Cancel"],
    )
    if action == "Provide a new name":
        new_filename = input("Enter the new filename: ")
        return "new_name", new_filename
    return ("overwrite", None) if action == "Overwrite" else ("cancel", None)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="A script for sharing music bounces in a variety of formats."
    )
    parser.add_argument("input_file", help="The audio file to convert")
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Use naming suitable for upload, stripping spaces and apostrophes",
    )
    return parser.parse_args()


@handle_keyboard_interrupt()
def main() -> None:
    """Convert to desired formats."""
    # Start the loading animation
    animation_thread = animation.start_animation()

    # Parse command-line arguments
    args = parse_arguments()
    input_file = args.input_file

    if len(sys.argv) < 2:  # Check for input file
        print("Please provide an input file.")
        sys.exit(1)
    input_file = sys.argv[1]
    if not os.path.isfile(input_file):  # Check that input file exists
        print(colored(f"The file {input_file} does not exist. Aborting.", "red"))
        sys.exit(1)

    # Determine bit depth
    bit_depth = find_bit_depth(input_file)

    # Stop the animation
    animation.stop_animation(animation_thread)

    # Prompt for conversion options, exit if aborted
    formats = show_format_options()
    if formats is None:
        sys.exit(1)

    # MP3 shame
    if "Convert to MP3" in formats["options"]:
        print(colored("MP3 is bad and you should feel bad.\n", "yellow"))

    # Generate filename and perform conversions
    new_filename = clean_filename(input_file, "upload" if args.upload else "local")

    # Call the new file_exists_prompt function before performing conversions
    action, _ = prompt_if_file_exists(new_filename)
    if action == "cancel":
        print(colored("Conversion aborted because of existing file.", "yellow"))
        sys.exit(1)

    perform_conversions(formats, input_file, OUTPUT_PATH, new_filename, bit_depth)


if __name__ == "__main__":
    main()
