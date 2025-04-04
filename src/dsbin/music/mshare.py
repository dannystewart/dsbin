#!/usr/bin/env python3

"""A script for sharing music bounces in a variety of formats.

This script is designed to convert music bounces to WAV, FLAC, and MP3 files for easy sharing with
people who need or prefer different formats or for uploading to different platforms. Also includes
bit depth conversion for 24-bit files.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import inquirer
from logician import Logician
from polykit import polykit_setup
from polykit.cli import ArgParser, halo_progress
from polykit.parsers import color as colored
from polykit.shell import handle_interrupt
from walking_man import walking_man

from dsbin.media import MediaManager

if TYPE_CHECKING:
    import argparse

polykit_setup()


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
    completion_message: str
    available_bit_depths: list[int] = field(default_factory=lambda: [16, 24])


class MusicShare:
    """A class for sharing music bounces in a variety of formats."""

    OUTPUT_PATH: ClassVar[Path] = Path.home() / "Downloads"

    def __init__(self, input_file: Path, bit_depth: int, upload: bool = False):
        self.logger = Logician.get_logger(simple=True)
        self.input_file = input_file
        self.bit_depth = bit_depth
        self.upload = upload

    def perform_conversions(self) -> None:
        """Perform the conversions selected by the user based on conversion options."""
        answers = self.get_user_format_selections()
        conversion_options = self.get_conversion_settings(answers["options"])

        for option, settings in conversion_options.items():
            if option in answers["options"]:
                output_file = self.OUTPUT_PATH / settings.filename
                if output_file.is_file():
                    self.logger.warning("File %s already exists.", output_file)
                    action = inquirer.list_input(
                        "Choose an action",
                        choices=[
                            "Overwrite",
                            "Provide a new name",
                            "Cancel",
                        ],
                    )
                    if action == "Cancel":
                        self.logger.warning("Conversion canceled by user.")
                        continue
                    if action == "Provide a new name":
                        custom_filename = input("Enter the new filename: ")
                        settings.filename = Path(custom_filename)

                with halo_progress(
                    str(settings.filename),
                    start_message=settings.message,
                    end_message=settings.completion_message,
                    fail_message="Failed",
                ) as spinner:
                    success, message = self.convert_file(settings)
                    if not success:
                        spinner.fail(message)

        self.logger.info("All conversions complete!")

    def get_available_options(self) -> list[str]:
        """Return the available conversion options based on the bit depth."""
        available_options = [
            "Copy original as WAV",
            "Convert to 16-bit WAV",
            "Convert to 16-bit FLAC",
            "Convert to MP3",
        ]

        if self.bit_depth == 24:
            available_options.insert(3, "Convert to 24-bit FLAC")

        return available_options

    def get_user_format_selections(self) -> dict[str, list[str]]:
        """Prompt the user for conversion options from an inquirer menu."""
        questions = [
            inquirer.Checkbox(
                "options",
                message="Select conversion options",
                choices=self.get_available_options(),
                carousel=True,
            ),
        ]
        answers = inquirer.prompt(questions)
        if answers is None:
            sys.exit(1)

        # MP3 shame
        if "Convert to MP3" in answers["options"]:
            print(colored("MP3 is bad and you should feel bad.\n", "cyan"))

        return answers

    def get_conversion_settings(self, settings: list[str]) -> dict[str, ConversionSettings]:
        """Construct the conversion options dictionary."""
        base_name = self.OUTPUT_PATH / self.clean_name("upload" if self.upload else "local")
        input_ext = self.input_file.suffix.lower()
        is_wav = input_ext == ".wav"

        # Determine if we need bit depth suffixes
        add_wav = "Convert to 16-bit WAV" in settings and "Copy original as WAV" in settings
        add_flac = "Convert to 16-bit FLAC" in settings and "Convert to 24-bit FLAC" in settings

        # Generate filenames
        filenames = self.get_filenames(base_name, add_wav, add_flac)

        return {
            "Copy original as WAV": self._get_wav_settings(filenames["wav"], is_wav),
            "Convert to 16-bit WAV": self._get_wav_16bit_settings(filenames["wav_16"]),
            "Convert to 16-bit FLAC": self._get_flac_16bit_settings(filenames["flac_16"]),
            "Convert to 24-bit FLAC": self._get_flac_24bit_settings(filenames["flac_24"]),
            "Convert to MP3": self._get_mp3_settings(filenames["mp3"]),
        }

    def convert_file(self, settings: ConversionSettings) -> tuple[bool, str]:
        """Perform an individual file conversion. Returns success status and message."""
        if self.bit_depth not in settings.available_bit_depths:
            return (
                False,
                f"Requires {settings.available_bit_depths} bit depth but the input is {self.bit_depth} bit.",
            )

        destination_path = self.OUTPUT_PATH / settings.filename
        command = settings.command.format(
            input_file=self.input_file, destination_path=destination_path
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

    def get_filenames(self, base_name: Path, add_wav: bool, add_flac: bool) -> dict[str, Path]:
        """Generate filenames for the output files."""
        return {
            "wav": self._get_name(base_name, "wav"),
            "wav_16": self._get_name(base_name, "wav", " (16-bit)" if add_wav else ""),
            "flac_16": self._get_name(base_name, "flac", " (16-bit)" if add_flac else ""),
            "flac_24": self._get_name(base_name, "flac", " (24-bit)" if add_flac else ""),
            "mp3": self._get_name(base_name, "mp3"),
        }

    def clean_name(self, naming_format: str) -> Path:
        """Generate formatted names for the output files. Removes versions and parentheticals."""
        filename_no_ext = self.input_file.stem
        clean_name_pattern = re.compile(
            r"( [0-9]+([._][0-9]+){2,3}([._][0-9]+)?[a-z]{0,2}$)|(\s*\(No [^)]*\))"
        )
        clean_name = clean_name_pattern.sub("", filename_no_ext)

        if naming_format == "upload":
            clean_name = clean_name.replace(" ", "-").replace("'", "")

        return Path(clean_name)

    def _get_wav_settings(self, filename: Path, is_wav: bool) -> ConversionSettings:
        """Create settings for original WAV conversion."""
        command = (
            f'cp "{self.input_file}" "{filename}"'
            if is_wav
            else f'ffmpeg -i "{self.input_file}" -y -acodec pcm_s{self.bit_depth}le "{filename}"'
        )
        return ConversionSettings(
            filename=filename,
            command=command,
            message="Copying" if is_wav else "Converting to WAV",
            completion_message="Copied:" if is_wav else "Converted to WAV:",
        )

    def _get_wav_16bit_settings(self, filename: Path) -> ConversionSettings:
        """Create settings for 16-bit WAV conversion."""
        return ConversionSettings(
            filename=filename,
            command=f'ffmpeg -i "{self.input_file}" -y -acodec pcm_s16le "{filename}"',
            message="Converting to 16-bit WAV",
            completion_message="Converted to 16-bit WAV:",
            available_bit_depths=[16],
        )

    def _get_flac_16bit_settings(self, filename: Path) -> ConversionSettings:
        """Create settings for 16-bit FLAC conversion."""
        return ConversionSettings(
            filename=filename,
            command=f'ffmpeg -i "{self.input_file}" -y -acodec flac -sample_fmt s16 "{filename}"',
            message="Converting to 16-bit FLAC",
            completion_message="Converted to 16-bit FLAC:",
        )

    def _get_flac_24bit_settings(self, filename: Path) -> ConversionSettings:
        """Create settings for 24-bit FLAC conversion."""
        return ConversionSettings(
            filename=filename,
            command=f'ffmpeg -i "{self.input_file}" -y -acodec flac -sample_fmt s32 -bits_per_raw_sample 24 "{filename}"',
            message="Converting to 24-bit FLAC",
            completion_message="Converted to 24-bit FLAC:",
        )

    def _get_mp3_settings(self, filename: Path) -> ConversionSettings:
        """Create settings for MP3 conversion."""
        return ConversionSettings(
            filename=filename,
            command=f'ffmpeg -i "{self.input_file}" -y -b:a 320k "{filename}"',
            message="Converting to MP3",
            completion_message="Converted to MP3:",
        )

    @staticmethod
    def _get_name(base_name: Path, extension: str, suffix: str = "") -> Path:
        """Generate a filename with an optional suffix."""
        return Path(f"{base_name}{suffix}.{extension}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = ArgParser(description=__doc__)
    parser.add_argument("input_file", help="the file to convert")
    parser.add_argument("--upload", action="store_true", help="use URL-safe filename for uploading")
    return parser.parse_args()


@handle_interrupt()
def main() -> None:
    """Convert to desired formats."""
    args = parse_arguments()
    input_file = Path(args.input_file)

    if not input_file.is_file():
        print(colored(f"The file {input_file} does not exist. Aborting.", "red"))
        sys.exit(1)

    with walking_man():  # Determine the bit depth so we know what options to show
        bit_depth = MediaManager().find_bit_depth(input_file)

    mshare = MusicShare(input_file, bit_depth, args.upload)
    mshare.perform_conversions()


if __name__ == "__main__":
    main()
