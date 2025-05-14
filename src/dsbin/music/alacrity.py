"""Converts files in a directory to ALAC, with additional formats and options.

This script is designed to convert files in the current directory to ALAC, preserving creation and
modification timestamps. Its primary use case is for converting old Logic bounces into smaller files
while preserving the original timestamps, which are important for referring back to project history.

The script can also convert files to FLAC, AIFF, or WAV, and can be used to convert individual files
as well as directories.
"""

from __future__ import annotations

from contextlib import contextmanager
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from natsort import natsorted
from polykit.cli import PolyArgs, confirm_action
from polykit.core import polykit_setup
from polykit.files import PolyFile
from polykit.formatters import color
from polykit.log import PolyLog

from dsbin.media import MediaManager

if TYPE_CHECKING:
    import argparse
    from collections.abc import Generator

polykit_setup()


@contextmanager
def conversion_list_context(file_name: str) -> Generator[None, None, None]:
    """Context manager to print a message at the start and end of a conversion."""
    try:
        print(f"Converting {file_name} ... ", end="")
        yield
    finally:
        print(color("done!", "green"))


class ConversionResult(StrEnum):
    """Result of the conversion process."""

    CONVERTED = "converted"
    EXISTS = "already_exists"
    FAILED = "failed"


class ALACrity:
    """Converts files in a directory to ALAC, with additional formats and options."""

    # Default and allowed file extensions
    DEFAULT_EXTS: ClassVar[list[str]] = [".aiff", ".aif", ".wav"]
    ALLOWED_EXTS: ClassVar[list[str]] = [".aiff", ".aif", ".wav", ".m4a", ".flac"]

    # Default target format and extension
    DEFAULT_SOURCE_EXTS: ClassVar[list[str]] = ["aiff", "aif", "wav"]
    DEFAULT_TARGET_EXT: ClassVar[str] = "m4a"

    # Undo settings
    UNDO_SOURCE_EXTS: ClassVar[list[str]] = ["m4a"]
    UNDO_TARGET_EXT: ClassVar[str] = "wav"

    # Supported file codecs
    FILE_CODECS: ClassVar[dict[str, str]] = {
        "flac": "flac",
        "aiff": "pcm_s16be",
        "wav": "pcm_s16le",
        "m4a": "alac",
    }

    def __init__(self, args: argparse.Namespace) -> None:
        self.media = MediaManager()
        self.logger = PolyLog.get_logger("alacrity", simple=True)

        # Initialize instance variables
        self.args: argparse.Namespace = args
        self.auto_mode: bool = True
        self.preserve_bit_depth: bool = self.args.preserve_depth
        self.paths: list[str] = []

        # Set default values for conversion options
        self.bit_depth = 16
        self.audio_bitrate = "320k"
        self.sample_rate = "44100"
        self.extension: str | None = None

        # Run the script
        self._configure_vars_from_args()
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
            self.logger.info("No files to convert.")
            return

        if converted_files and confirm_action("Do you want to remove the original files?"):
            successful, failed = PolyFile.delete(original_files, logger=None)
            self.logger.info("%d files trashed successfully.", len(successful))
            if failed:
                self.logger.warning("Failed to delete %d files.", len(failed))

    def _gather_files(self, path: str) -> list[Path]:
        """Gather the files or directories to process based on the given path. For directories, it
        uses the specified file extensions to filter files.

        Args:
            path: A string representing a file path or directory.

        Returns:
            A list of file paths to be processed.
        """
        list_args = {
            "extensions": self.exts_to_convert,
            "recursive": False,
        }

        if self.auto_mode:
            list_args["include_dotfiles"] = False

        path_obj = Path(path)
        if self.args.undo and path_obj.is_dir():  # For undo, only find M4A files
            files_to_process = list(path_obj.glob("*.m4a"))
        elif path_obj.is_file() and path_obj.suffix.lower()[1:] in self.exts_to_convert:
            files_to_process = [path_obj]
        elif path_obj.is_dir():
            files_to_process = PolyFile.list(path_obj, **list_args)
        else:
            self.logger.error(
                "The path '%s' is neither a directory nor a file with a valid extension.", path
            )
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
                    ctime, mtime = PolyFile.get_timestamps(input_path)
                    PolyFile.set_timestamps(output_path, ctime=ctime, mtime=mtime)
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
        if output_path.exists():
            return output_path, ConversionResult.EXISTS

        # Determine bit depth first
        if self.preserve_bit_depth:
            actual_bit_depth = self.media.find_bit_depth(input_path)
            if actual_bit_depth in {24, 32}:
                self.bit_depth = actual_bit_depth

                # Set the codec based on bit depth for WAV
                if self.extension == "wav":
                    if self.bit_depth == 24:
                        self.codec = "pcm_s24le"
                    elif self.bit_depth == 32:
                        self.codec = "pcm_s32le"
                    else:
                        self.codec = "pcm_s16le"

        if self.codec is None:  # Determine codec based on extension
            if self.extension is not None:  # Make sure the extension is not None
                self.codec = self.FILE_CODECS.get(self.extension, "alac")
            else:  # Otherwise, default to ALAC
                self.codec = "alac"

        with conversion_list_context(input_path.name):
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
                self.logger.error("Failed to convert %s: %s", input_path.name, str(e))
                return input_path, ConversionResult.FAILED

    def _configure_vars_from_args(self) -> None:
        """Set instance variables based on the parsed command-line arguments."""
        resolved_paths = []
        for path in self.args.paths:
            path_obj = Path(path)
            if "*" in str(path_obj) or "?" in str(path_obj):
                resolved_paths.extend(path_obj.parent.glob(path_obj.name))
            else:
                resolved_paths.append(path_obj)

        self.paths = natsorted([str(p) for p in resolved_paths])

        # Handle undo mode
        if self.args.undo:
            self.extension = self.UNDO_TARGET_EXT
            self.exts_to_convert = self.UNDO_SOURCE_EXTS
            self.codec = None  # Determine afterward based on bit depth
            self.preserve_bit_depth = True  # Always preserve bit depth when undoing
            self.auto_mode = False
            return

        # Normal mode processing
        self.auto_mode = not (
            self.args.flac
            or self.args.wav
            or self.args.aiff
            or any(
                getattr(self.args, ext.lstrip("."), False)
                for ext in self.ALLOWED_EXTS
                if ext.lstrip(".") != "aif"
            )
        )

        # Set the target extension based on arguments
        for ext in self.ALLOWED_EXTS:
            ext_without_dot = ext.lstrip(".")
            if getattr(self.args, ext_without_dot, False):
                self.extension = ext_without_dot
                break

        # Handle extension defaults
        if self.extension is None:
            self.extension = self.DEFAULT_TARGET_EXT

        self.exts_to_convert = self.DEFAULT_SOURCE_EXTS if self.auto_mode else self.ALLOWED_EXTS
        self.exts_to_convert = [
            ext for ext in self.exts_to_convert if ext.lstrip(".") != self.extension
        ]
        self.codec = self.FILE_CODECS.get(self.extension, "alac")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description=__doc__, lines=2)
    parser.add_argument("-f", "--flac", action="store_true", help="convert files to FLAC")
    parser.add_argument("-w", "--wav", action="store_true", help="convert files to WAV")
    parser.add_argument("-a", "--aiff", action="store_true", help="convert files to AIFF/AIF")
    parser.add_argument(
        "--preserve-depth", action="store_true", help="preserve bit depth if higher than 16-bit"
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="convert M4A files back to WAV (undoing default behavior)",
    )

    for ext in ALACrity.ALLOWED_EXTS:
        ext_without_dot = ext.lstrip(".")
        if ext_without_dot not in {"flac", "wav", "aiff"}:
            parser.add_argument(
                f"--{ext_without_dot}",
                action="store_true",
                help=f"Convert files to {ext_without_dot.upper()}",
            )

    paths_help = "file(s) or directory of files to convert or wildcard pattern (e.g. *.m4a) (defaulting to current directory)"
    parser.add_argument("paths", nargs="*", default=[Path.cwd()], help=paths_help)

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()
    ALACrity(args)
