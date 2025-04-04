"""Converts files in a directory to ALAC, with additional formats and options.

This script is designed to convert files in the current directory to ALAC, preserving creation and
modification timestamps. Its primary use case is for converting old Logic bounces into smaller files
while preserving the original timestamps, which are important for referring back to project history.

The script can also convert files to FLAC, AIFF, or WAV, and can be used to convert individual files
as well as directories.
"""

from __future__ import annotations

import argparse
from enum import StrEnum
from pathlib import Path
from typing import ClassVar

from natsort import natsorted
from polykit import polykit_setup
from polykit.cli import confirm_action, conversion_list_context
from polykit.parsers import print_color

from dsbin.files import FileManager
from dsbin.media import MediaManager

polykit_setup()


class ALACrity:
    """Converts files in a directory to ALAC, with additional formats and options."""

    # Default and allowed file extensions
    DEFAULT_EXTS: ClassVar[list[str]] = [".aiff", ".aif", ".wav"]
    ALLOWED_EXTS: ClassVar[list[str]] = [".aiff", ".aif", ".wav", ".m4a", ".flac"]

    # Supported file codecs
    FILE_CODECS: ClassVar[dict[str, str]] = {
        "flac": "flac",
        "aiff": "pcm_s16be",
        "wav": "pcm_s16le",
        "m4a": "alac",
    }

    def __init__(self, args: argparse.Namespace) -> None:
        self.files = FileManager()
        self.media = MediaManager()

        # Set default values for conversion options
        self.bit_depth = 16
        self.audio_bitrate = "320k"
        self.sample_rate = "44100"
        self.extension: str | None = None

        # Run the script
        self._configure_vars_from_args(args)
        self.run_conversion()

    def run_conversion(self) -> None:
        """Gather specified files, convert them, and prompt for deletion of the originals."""
        converted_files = []
        original_files = []
        skipped_files = []

        for path in self.paths:
            files_to_process = self._gather_files(path)
            if not files_to_process:
                continue

            converted, original, skipped = self.gather_and_process_files(files_to_process)
            converted_files.extend(converted)
            original_files.extend(original)
            skipped_files.extend(skipped)

        if not original_files and not skipped_files:
            print_color("No files to convert.", "green")
            return

        if converted_files and confirm_action("Do you want to remove the original files?"):
            self.files.delete(original_files, show_individual=False)

        if skipped_files and confirm_action(
            "Do you want to remove the skipped original files (WAV files with existing M4A)?"
        ):
            self.files.delete(skipped_files, show_individual=False)

    def _gather_files(self, path: str) -> list[Path]:
        """Gather the files or directories to process based on the given path. For directories, it
        uses the specified file extensions to filter files.

        Args:
            path: A string representing a file path or directory.

        Returns:
            A list of file paths to be processed.
        """
        list_args = {
            "exts": [ext.lstrip(".") for ext in self.exts_to_convert],
            "recursive": False,
        }
        files_to_process = []

        if self.auto_mode:
            list_args["include_hidden"] = False

        path_obj = Path(path)
        if path_obj.is_file() and path_obj.suffix.lower() in self.ALLOWED_EXTS:
            files_to_process = [path_obj]
        elif path_obj.is_dir():
            files_to_process = self.files.list(path_obj, **list_args)
        else:
            print(f"The path '{path}' is neither a directory nor a file.")
            return []

        return natsorted(files_to_process)

    def gather_and_process_files(
        self, files_to_process: list[Path]
    ) -> tuple[list[Path], list[Path], list[Path]]:
        """Convert the gathered files, track the conversion result for each file, and preserve the
        original timestamps for successfully converted files.

        Args:
            files_to_process: A list of file paths to be converted.

        Returns:
            A tuple containing three lists:
            - converted_files: Paths of successfully converted files.
            - original_files: Paths of original files that were successfully converted.
            - skipped_files: Paths of files skipped due to existing converted versions.
        """
        converted_files = []
        original_files = []
        skipped_files = []

        for input_path in files_to_process:
            output_path, status = self.handle_file_conversion(input_path)

            match status:
                case ConversionResult.CONVERTED:
                    converted_files.append(output_path)
                    original_files.append(input_path)
                    ctime, mtime = self.files.get_timestamps(input_path)
                    self.files.set_timestamps(output_path, ctime=ctime, mtime=mtime)
                case ConversionResult.EXISTS:
                    skipped_files.append(input_path)
                case ConversionResult.FAILED:
                    pass  # Files with status "failed" are not added to any list

        return converted_files, original_files, skipped_files

    def handle_file_conversion(self, input_path: Path) -> tuple[Path, ConversionResult]:
        """Convert a single file to the specified format using ffmpeg_audio, including checking for
        existing files and preserving bit depth if specified.

        Args:
            input_path: The path of the file to be converted.

        Returns:
            A tuple containing:
            - output_path: The path of the converted file (or None if conversion failed).
            - status: The status of the conversion (ConversionStatus enum value).
        """
        output_path = input_path.with_suffix(f".{self.extension}")
        output_filename = output_path.name

        if output_path.exists():
            return output_path, ConversionResult.EXISTS

        if self.preserve_bit_depth:
            actual_bit_depth = self.media.find_bit_depth(input_path)
            if actual_bit_depth in {24, 32}:
                self.bit_depth = actual_bit_depth

        with conversion_list_context(output_filename):
            try:
                self.media.ffmpeg_audio(
                    input_files=input_path,
                    output_format=self.extension or "m4a",
                    codec=self.codec,
                    bit_depth=self.bit_depth,
                    audio_bitrate=self.audio_bitrate,
                    sample_rate=self.sample_rate,
                    preserve_metadata=True,
                    show_output=False,
                )
                return output_path, ConversionResult.CONVERTED
            except Exception as e:
                print_color(f"\nFailed to convert {input_path.name}: {e}", "red")
                return input_path, ConversionResult.FAILED

    def _configure_vars_from_args(self, args: argparse.Namespace) -> None:
        """Set instance variables based on the parsed command-line arguments."""
        resolved_paths = []
        for path in args.paths:
            path_obj = Path(path)
            if "*" in str(path_obj) or "?" in str(path_obj):
                resolved_paths.extend(path_obj.parent.glob(path_obj.name))
            else:
                resolved_paths.append(path_obj)

        self.paths = natsorted([str(p) for p in resolved_paths])
        self.preserve_bit_depth = args.max
        self.auto_mode = not (
            args.flac
            or args.wav
            or args.aiff
            or any(
                getattr(args, ext.lstrip("."), False)
                for ext in self.ALLOWED_EXTS
                if ext.lstrip(".") != "aif"
            )
        )

        for ext in self.ALLOWED_EXTS:
            ext_without_dot = ext.lstrip(".")
            if getattr(args, ext_without_dot):
                self.extension = ext_without_dot
                break
        if self.extension is None:
            self.extension = "m4a"

        self.exts_to_convert = self.DEFAULT_EXTS if self.auto_mode else self.ALLOWED_EXTS
        self.exts_to_convert = [
            ext for ext in self.exts_to_convert if ext.lstrip(".") != self.extension
        ]
        self.codec = self.FILE_CODECS.get(self.extension, "alac")


class ConversionResult(StrEnum):
    """Result of the conversion process."""

    CONVERTED = "converted"
    EXISTS = "already_exists"
    FAILED = "failed"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert audio files to different formats")
    parser.add_argument("-f", "--flac", action="store_true", help="Convert files to FLAC")
    parser.add_argument("-w", "--wav", action="store_true", help="Convert files to WAV")
    parser.add_argument("-a", "--aiff", action="store_true", help="Convert files to AIFF/AIF")
    parser.add_argument(
        "--max", action="store_true", help="Preserve maximum bit depth of the files"
    )

    for ext in ALACrity.ALLOWED_EXTS:
        ext_without_dot = ext.lstrip(".")
        if ext_without_dot not in {"flac", "wav", "aiff"}:
            parser.add_argument(
                f"--{ext_without_dot}",
                action="store_true",
                help=f"Convert files to {ext_without_dot.upper()}",
            )

    paths_help = "File(s) or directory of files to convert or wildcard pattern (e.g., *.m4a) (defaulting to current directory)"
    parser.add_argument("paths", nargs="*", default=[Path.cwd()], help=paths_help)

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()
    ALACrity(args)
