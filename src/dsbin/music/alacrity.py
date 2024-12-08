"""
Converts files in a directory to ALAC, with additional formats and options.

This script is designed to convert files in the current directory to ALAC, preserving
creation and modification timestamps. Its primary use case is for converting old Logic
bounces into smaller files while preserving the original timestamps, which are important
for referring back to project version history.

The script can also convert files to FLAC, AIFF, or WAV, and can be used to convert
individual files as well as directories.
"""

from __future__ import annotations

import argparse
import glob
import os

from natsort import natsorted

from dsutil import configure_traceback
from dsutil.files import delete_files, list_files
from dsutil.macos import get_timestamps, set_timestamps
from dsutil.media import ffmpeg_audio, find_bit_depth
from dsutil.progress import conversion_list_context
from dsutil.shell import confirm_action
from dsutil.text import print_colored

configure_traceback()

DEFAULT_EXTS = [".aiff", ".aif", ".wav"]
ALLOWED_EXTS = [".aiff", ".aif", ".wav", ".m4a", ".flac"]


class ALACrity:
    """Converts files in a directory to ALAC, with additional formats and options."""

    def __init__(self, args: argparse.Namespace) -> None:
        # Supported file codecs
        self.file_codecs = {
            "flac": "flac",
            "aiff": "pcm_s16be",
            "wav": "pcm_s16le",
            "m4a": "alac",
        }

        # Set default values for conversion options
        self.bit_depth = 16
        self.audio_bitrate = "320k"
        self.sample_rate = "44100"
        self.extension = None

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
            print_colored("No files to convert.", "green")
            return

        if converted_files and confirm_action("Do you want to remove the original files?"):
            delete_files(original_files, show_individual=False)

        if skipped_files and confirm_action(
            "Do you want to remove the skipped original files (WAV files with existing M4A)?"
        ):
            delete_files(skipped_files, show_individual=False)

    def _gather_files(self, path: str) -> list[str]:
        """
        Gather the files or directories to process based on the given path. For directories, it uses
        the specified file extensions to filter files.

        Args:
            path: A string representing a file path or directory.

        Returns:
            A list of file paths to be processed.
        """
        list_files_args = {
            "extensions": [ext.lstrip(".") for ext in self.exts_to_convert],
            "recursive": False,
        }
        files_to_process = []

        if self.auto_mode:
            list_files_args["include_hidden"] = False

        if os.path.isfile(path) and path.lower().endswith(tuple(ALLOWED_EXTS)):
            files_to_process = [path]
        elif os.path.isdir(path):
            files_to_process = list_files(path, **list_files_args)
        else:
            print(f"The path '{path}' is neither a directory nor a file.")
            return []

        return natsorted(files_to_process)

    def gather_and_process_files(
        self, files_to_process: list[str]
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Convert the gathered files, track the conversion result for each file, and preserve the
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

            if status == "converted":
                converted_files.append(output_path)
                original_files.append(input_path)
                ctime, mtime = get_timestamps(input_path)
                set_timestamps(output_path, ctime=ctime, mtime=mtime)
            elif status == "already_exists":
                skipped_files.append(input_path)
            # Files with status "failed" are not added to any list

        return converted_files, original_files, skipped_files

    def handle_file_conversion(self, input_path: str) -> tuple[str, str]:
        """
        Convert a single file to the specified format using ffmpeg_audio, including checking for
        existing files and preserving bit depth if specified.

        Args:
            input_path: The path of the file to be converted.

        Returns:
            A tuple containing:
            - output_path: The path of the converted file (or None if conversion failed).
            - status: A string indicating the status of the conversion
                ("converted", "already_exists", or "failed").
        """
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}.{self.extension}"
        input_filename = os.path.basename(input_path)
        output_filename = os.path.basename(output_path)

        if os.path.exists(output_path):
            return output_path, "already_exists"

        if self.preserve_bit_depth:
            actual_bit_depth = find_bit_depth(input_path)
            if actual_bit_depth in [24, 32]:
                self.bit_depth = actual_bit_depth

        with conversion_list_context(output_filename):
            try:
                ffmpeg_audio(
                    input_files=input_path,
                    output_format=self.extension,
                    codec=self.codec,
                    bit_depth=self.bit_depth,
                    audio_bitrate=self.audio_bitrate,
                    sample_rate=self.sample_rate,
                    preserve_metadata=True,
                    show_output=False,
                )
                return output_path, "converted"
            except Exception as e:
                print_colored(f"\nFailed to convert {input_filename}: {e}", "red")
                return input_path, "failed"

    @staticmethod
    def _handle_existing_file(output_path: str) -> bool:
        """
        Check for an existing file and prompt to confirm whether to overwrite if needed.

        Args:
            output_path: The path where the converted file would be saved.

        Returns:
            True if the file doesn't exist or user confirms overwrite, False otherwise.
        """
        if os.path.exists(output_path):
            print_colored(f"File '{output_path}' already exists.", "yellow")
            if confirm_action("Overwrite?"):
                os.remove(output_path)
                return True
            return False
        return True

    def _configure_vars_from_args(self, args: argparse.Namespace) -> None:
        """Set instance variables based on the parsed command-line arguments."""
        resolved_paths = []
        for path in args.paths:
            if "*" in path or "?" in path:
                resolved_paths.extend(glob.glob(path))
            else:
                resolved_paths.append(path)

        self.paths = natsorted(resolved_paths)
        self.preserve_bit_depth = args.max
        self.auto_mode = not (
            args.flac
            or args.wav
            or args.aiff
            or any(
                getattr(args, ext.lstrip("."), False)
                for ext in ALLOWED_EXTS
                if ext.lstrip(".") != "aif"
            )
        )

        for ext in ALLOWED_EXTS:
            ext_without_dot = ext.lstrip(".")
            if getattr(args, ext_without_dot):
                self.extension = ext_without_dot
                break
        if self.extension is None:
            self.extension = "m4a"

        self.exts_to_convert = DEFAULT_EXTS if self.auto_mode else ALLOWED_EXTS
        self.exts_to_convert = [
            ext for ext in self.exts_to_convert if ext.lstrip(".") != self.extension
        ]
        self.codec = self.file_codecs.get(self.extension, "alac")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Convert audio files to different formats")

    parser.add_argument("-f", "--flac", action="store_true", help="Convert files to FLAC")
    parser.add_argument("-w", "--wav", action="store_true", help="Convert files to WAV")
    parser.add_argument("-a", "--aiff", action="store_true", help="Convert files to AIFF/AIF")
    parser.add_argument(
        "--max", action="store_true", help="Preserve maximum bit depth of the files"
    )

    for ext in ALLOWED_EXTS:
        ext_without_dot = ext.lstrip(".")
        if ext_without_dot not in ["flac", "wav", "aiff"]:
            parser.add_argument(
                f"--{ext_without_dot}",
                action="store_true",
                help=f"Convert files to {ext_without_dot.upper()}",
            )

    paths_help = "File(s) or directory of files to convert or wildcard pattern (e.g., *.m4a) (defaulting to current directory)"
    parser.add_argument("paths", nargs="*", default=[os.getcwd()], help=paths_help)

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    ALACrity(args)
