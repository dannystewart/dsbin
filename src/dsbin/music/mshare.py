#!/usr/bin/env python3

"""A script for sharing music bounces in a variety of formats.

This script is designed to convert music bounces to WAV, FLAC, and MP3 files for easy sharing with
people who need or prefer different formats or for uploading to different platforms. Also includes
bit depth conversion for 24-bit files.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import inquirer

from dsutil import animation, configure_traceback
from dsutil.media import find_bit_depth
from dsutil.progress import halo_progress
from dsutil.shell import handle_keyboard_interrupt
from dsutil.text import color as colored

configure_traceback()

HOME_DIR = Path.home()
OUTPUT_PATH = HOME_DIR / "Downloads"


@dataclass
class ConversionSettings:
    """Settings for a specific conversion operation.

    Args:
        filename: The output filename.
        command: The ffmpeg command to execute.
        message: The message to show during conversion.
        completed_message: The message to show after successful conversion.
        available_bit_depths: List of acceptable input bit depths.
    """

    filename: Path
    command: str
    message: str
    completed_message: str
    available_bit_depths: list[int] = field(default_factory=lambda: [16, 24, 32])


def show_format_options() -> dict[str, list[str]] | None:
    """Prompt the user for conversion options from an inquirer menu."""
    questions = [
        inquirer.Checkbox(
            "options",
            message="Select conversion options",
            choices=[
                "Copy original as WAV",
                "Convert to 16-bit WAV",
                "Convert to 16-bit FLAC",
                "Convert to 24-bit FLAC",
                "Convert to MP3",
            ],
            carousel=True,
        ),
    ]
    return inquirer.prompt(questions)


def clean_filename(input_file: Path, naming_format: str) -> Path:
    """Generate sanitized and formatted filenames for the output files.

    Removes version numbers and parentheticals starting with "No" (e.g. No Vocals, No Drums).

    Notes:
    - The WAV and FLAC files are formatted with hyphens instead of spaces.
    - The MP3 file is formatted with spaces instead of hyphens.

    Args:
        input_file: The path to the input file.
        naming_format: The naming format to use (e.g. "Local", "For upload").
    """
    filename_no_ext = input_file.stem
    clean_name_pattern = re.compile(
        r"( [0-9]+([._][0-9]+){2,3}([._][0-9]+)?[a-z]{0,2}$)|(\s*\(No [^)]*\))"
    )
    clean_name = clean_name_pattern.sub("", filename_no_ext)

    if naming_format == "upload":
        clean_name = clean_name.replace(" ", "-").replace("'", "")

    return Path(clean_name)


def convert_file(
    input_file: Path, output_path: Path, settings: ConversionSettings, bit_depth: int
) -> tuple[bool, str]:
    """Perform an individual conversion.

    Args:
        input_file: The path to the input file.
        output_path: The path to the output directory.
        settings: The settings for the conversion.
        bit_depth: The bit depth of the input file.

    Returns:
        A tuple of whether the operation was successful and the success/error message to use.
    """
    destination_path = output_path / settings.filename

    if bit_depth not in settings.available_bit_depths:
        return (
            False,
            f"Requires {settings.available_bit_depths} bit depth but the input is {bit_depth} bit.",
        )
    command = settings.command.format(input_file=input_file, destination_path=destination_path)

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


def _get_filename(base_name: Path, extension: str, suffix: str = "") -> Path:
    """Generate a filename with an optional suffix."""
    return Path(f"{base_name}{suffix}.{extension}")


def get_conversion_settings(
    input_file: Path,
    output_path: Path,
    output_filename: Path,
    selections: list[str],
    bit_depth: int,
) -> dict[str, ConversionSettings]:
    """Construct the conversion options dictionary."""
    base_name = output_path / output_filename

    # Determine if we need bit depth suffixes based on selected options
    needs_wav_suffix = (
        "Convert to 16-bit WAV" in selections and "Copy original as WAV" in selections
    )
    needs_flac_suffix = (
        "Convert to 16-bit FLAC" in selections and "Convert to 24-bit FLAC" in selections
    )

    # Generate filenames with conditional suffixes
    wav_name = _get_filename(base_name, "wav")
    wav_16_bit_name = _get_filename(base_name, "wav", " (16-bit)" if needs_wav_suffix else "")
    flac_16_bit_name = _get_filename(base_name, "flac", " (16-bit)" if needs_flac_suffix else "")
    flac_24_bit_name = _get_filename(base_name, "flac", " (24-bit)" if needs_flac_suffix else "")
    mp3_name = _get_filename(base_name, "mp3")

    # Determine if input is WAV or needs conversion
    input_ext = input_file.suffix.lower()
    is_wav = input_ext == ".wav"
    wav_command = (
        f'cp "{input_file}" "{wav_name}"'
        if is_wav
        else f'ffmpeg -i "{input_file}" -y -acodec pcm_s{bit_depth}le "{wav_name}"'
    )

    return {
        "Copy original as WAV": ConversionSettings(
            filename=wav_name,
            command=wav_command,
            message="Copying" if is_wav else "Converting to WAV",
            completed_message="Copied:" if is_wav else "Converted to WAV:",
        ),
        "Convert to 16-bit WAV": ConversionSettings(
            filename=wav_16_bit_name,
            command=f'ffmpeg -i "{input_file}" -y -acodec pcm_s16le "{wav_16_bit_name}"',
            message="Converting to 16-bit WAV",
            completed_message="Converted to 16-bit WAV:",
            available_bit_depths=[16],
        ),
        "Convert to 16-bit FLAC": ConversionSettings(
            filename=flac_16_bit_name,
            command=f'ffmpeg -i "{input_file}" -y -acodec flac -sample_fmt s16 "{flac_16_bit_name}"',
            message="Converting to 16-bit FLAC",
            completed_message="Converted to 16-bit FLAC:",
        ),
        "Convert to 24-bit FLAC": ConversionSettings(
            filename=flac_24_bit_name,
            command=f'ffmpeg -i "{input_file}" -y -acodec flac -sample_fmt s32 -bits_per_raw_sample 24 "{flac_24_bit_name}"',
            message="Converting to 24-bit FLAC",
            completed_message="Converted to 24-bit FLAC:",
        ),
        "Convert to MP3": ConversionSettings(
            filename=mp3_name,
            command=f'ffmpeg -i "{input_file}" -y -b:a 320k "{mp3_name}"',
            message="Converting to MP3",
            completed_message="Converted to MP3:",
        ),
    }


def perform_conversions(
    answers: dict[str, list[str]],
    input_file: Path,
    output_path: Path,
    output_filename: Path,
    bit_depth: int,
) -> None:
    """Perform the conversions selected by the user based on a dictionary of conversion options.

    Args:
        answers: The answers to the conversion options prompt.
        input_file: The path to the input file.
        output_path: The path to the output directory.
        output_filename: The clean base filename for the output file.
        bit_depth: The bit depth of the input file.
    """
    conversion_options = get_conversion_settings(
        input_file, output_path, output_filename, answers["options"], bit_depth
    )

    for option, settings in conversion_options.items():
        if option in answers["options"]:
            action, new_filename = prompt_if_file_exists(settings.filename)
            if action == "cancel":
                print(colored("Conversion canceled by user.", "yellow"))
                continue
            if action == "new_name" and new_filename is not None:
                settings.filename = new_filename

            with halo_progress(
                filename=str(settings.filename),
                start_message=settings.message,
                end_message=settings.completed_message,
                fail_message="Failed",
            ) as spinner:
                success, message = convert_file(input_file, output_path, settings, bit_depth)
                if not success:
                    spinner.fail(message)

    print(colored("\nAll conversions complete!", "green"))


def prompt_if_file_exists(output_file: Path | None) -> tuple[str, Path | None]:
    """Check if the output file exists with the exact same name and extension.

    Prompt the user to choose between overwriting, providing a new name, or canceling.

    Args:
        output_file: The path to the output file.

    Returns:
        A tuple (action, new_filename) where action is 'overwrite', 'new_name', or 'cancel'.
    """
    if output_file is None or not output_file.is_file():
        return "none", None
    print(f"File {output_file} already exists.")
    action = inquirer.list_input(
        "Choose an action",
        choices=["Overwrite", "Provide a new name", "Cancel"],
    )
    if action == "Provide a new name":
        new_filename = input("Enter the new filename: ")
        return "new_name", Path(new_filename)
    return ("overwrite", None) if action == "Overwrite" else ("cancel", None)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="A script for sharing music bounces in a variety of formats."
    )
    parser.add_argument("input_file", help="The audio file to convert")
    parser.add_argument("--upload", action="store_true", help="use URL-safe filename for uploading")
    return parser.parse_args()


@handle_keyboard_interrupt()
def main() -> None:
    """Convert to desired formats."""
    # Start the loading animation
    animation_thread = animation.start_animation()

    # Parse command-line arguments
    args = parse_arguments()
    input_file = Path(args.input_file)

    if not input_file.is_file():
        print(colored(f"The file {input_file} does not exist. Aborting.", "red"))
        sys.exit(1)

    # Determine the bit depth so we know what options to show
    bit_depth = find_bit_depth(str(input_file))

    # Stop the animation once we have the bit depth
    animation.stop_animation(animation_thread)

    # Prompt for conversion options, or exit if aborted
    formats = show_format_options()
    if formats is None:
        sys.exit(1)

    # MP3 shame
    if "Convert to MP3" in formats["options"]:
        print(colored("MP3 is bad and you should feel bad.\n", "cyan"))

    # Generate the output filename and perform the conversions
    new_filename = clean_filename(input_file, "upload" if args.upload else "local")

    # Check if file exists before performing conversions
    action, _ = prompt_if_file_exists(new_filename)
    if action == "cancel":
        print(colored("Conversion aborted because of existing file.", "yellow"))
        sys.exit(1)

    perform_conversions(formats, input_file, OUTPUT_PATH, new_filename, bit_depth)


if __name__ == "__main__":
    main()
