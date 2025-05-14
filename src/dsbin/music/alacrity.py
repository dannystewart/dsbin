"""Converts files in a directory to ALAC, with additional formats and options.

This script is designed to convert files in the current directory to ALAC, preserving creation and
modification timestamps. Its primary use case is for converting old Logic bounces into smaller files
while preserving the original timestamps, which are important for referring back to project history.

The script can also convert files to FLAC, AIFF, or WAV, and can be used to convert individual files
as well as directories.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
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


class FormatCategory(StrEnum):
    """Categories of audio formats."""

    LOSSLESS = "lossless"
    LOSSY = "lossy"
    UNCOMPRESSED = "uncompressed"


@dataclass
class AudioFormat:
    """Represents an audio file format with its properties."""

    name: str  # Format name (e.g., "ALAC")
    extension: str  # Extension without dot (e.g., "m4a")
    codec: str  # ffmpeg codec name (e.g., "alac")
    category: FormatCategory  # Type of format (lossless, lossy, uncompressed)
    container: str | None = None  # Container format if different from extension

    @property
    def extension_with_dot(self) -> str:
        """Get the extension with a leading dot."""
        return f".{self.extension}"

    def get_codec_for_bit_depth(self, bit_depth: int) -> str:
        """Get the appropriate codec based on bit depth."""
        if self.name == "WAV":
            if bit_depth == 24:
                return "pcm_s24le"
            if bit_depth == 32:
                return "pcm_s32le"
            return "pcm_s16le"
        return self.codec


class ConversionResult(StrEnum):
    """Result of the conversion process."""

    CONVERTED = "converted"
    EXISTS = "already_exists"
    FAILED = "failed"


class ALACrity:
    """Converts files in a directory to ALAC, with additional formats and options."""

    # Define all supported audio formats
    FORMATS: ClassVar[dict[str, AudioFormat]] = {
        "alac": AudioFormat(
            name="ALAC",
            extension="m4a",
            codec="alac",
            category=FormatCategory.LOSSLESS,
        ),
        "flac": AudioFormat(
            name="FLAC",
            extension="flac",
            codec="flac",
            category=FormatCategory.LOSSLESS,
        ),
        "wav": AudioFormat(
            name="WAV",
            extension="wav",
            codec="pcm_s16le",
            category=FormatCategory.UNCOMPRESSED,
        ),
        "aiff": AudioFormat(
            name="AIFF",
            extension="aiff",
            codec="pcm_s16be",
            category=FormatCategory.UNCOMPRESSED,
        ),
        "aif": AudioFormat(
            name="AIFF",
            extension="aif",
            codec="pcm_s16be",
            category=FormatCategory.UNCOMPRESSED,
        ),
    }

    # Default settings
    DEFAULT_TARGET_FORMAT: ClassVar[AudioFormat] = FORMATS["alac"]
    DEFAULT_SOURCE_EXTENSIONS: ClassVar[list[str]] = ["aiff", "aif", "wav"]

    # Undo settings
    UNDO_TARGET_FORMAT: ClassVar[AudioFormat] = FORMATS["wav"]
    UNDO_SOURCE_EXTENSIONS: ClassVar[list[str]] = ["m4a"]

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

        # Target format will be set in _configure_vars_from_args
        self.target_format: AudioFormat | None = None
        self.source_extensions: list[str] = []

        # Run the script
        self._configure_vars_from_args()
        self.process_files()

    def _configure_vars_from_args(self) -> None:
        """Set instance variables based on the parsed command-line arguments."""
        # Resolve paths
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
            self.target_format = self.UNDO_TARGET_FORMAT
            self.source_extensions = self.UNDO_SOURCE_EXTENSIONS
            self.preserve_bit_depth = True
            self.auto_mode = False
            return

        # Determine if we're in auto mode
        self.auto_mode = not any(
            getattr(self.args, fmt.extension, False) for fmt in self.FORMATS.values()
        )

        # Set target format based on arguments
        for fmt in self.FORMATS.values():
            if getattr(self.args, fmt.extension, False):
                self.target_format = fmt
                break

        # Use default target if none specified
        if self.target_format is None:
            self.target_format = self.DEFAULT_TARGET_FORMAT

        # Set source extensions
        if self.auto_mode:
            self.source_extensions = self.DEFAULT_SOURCE_EXTENSIONS
        else:
            self.source_extensions = [
                fmt.extension
                for fmt in self.FORMATS.values()
                if fmt.extension != self.target_format.extension
            ]

    def process_files(self) -> None:
        """Gather specified files, convert them, and prompt for deletion of the originals."""
        converted_files = []
        original_files = []
        skipped_files = []

        for path in self.paths:
            files_to_process = self._gather_files(path)
            if not files_to_process:
                continue

            converted, original, skipped = self.handle_conversion(files_to_process)
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
        path_obj = Path(path)

        # For a specific file
        if path_obj.is_file():
            if path_obj.suffix.lower()[1:] in self.source_extensions:
                return [path_obj]
            self.logger.error("The file '%s' does not have a valid extension for conversion.", path)
            return []

        # For a directory
        if path_obj.is_dir():
            # Use glob patterns for simplicity and consistency
            files = []
            for ext in self.source_extensions:
                files.extend(path_obj.glob(f"*.{ext}"))
            return natsorted(files)

        self.logger.error("The path '%s' is neither a directory nor a file.", path)
        return []

    def handle_conversion(self, file_list: list[Path]) -> tuple[list[Path], list[Path], list[Path]]:
        """Convert the gathered files, track the conversion result for each file, and preserve the
        original timestamps for successfully converted files.

        Args:
            file_list: A list of file paths to be converted.

        Returns:
            A tuple containing three lists:
                - converted_files: Paths of successfully converted files.
                - original_files: Paths of original files that were successfully converted.
                - skipped_files: Paths of files skipped due to existing converted versions.
        """
        converted_files = []
        original_files = []
        skipped_files = []

        for input_path in file_list:
            output_path, status = self.convert_file(input_path)

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

    def convert_file(self, input_path: Path) -> tuple[Path, ConversionResult]:
        """Convert a single file to the specified format using ffmpeg_audio, including checking for
        existing files and preserving bit depth if specified.

        Args:
            input_path: The path of the file to be converted.

        Returns:
            A tuple containing:
                - output_path: The path of the converted file (or None if conversion failed).
                - status: The status of the conversion (ConversionStatus enum value).
        """
        if self.target_format is None:
            self.logger.error("No target format specified.")
            return input_path, ConversionResult.FAILED

        output_path = input_path.with_suffix(f".{self.target_format.extension}")

        if output_path.exists():
            return output_path, ConversionResult.EXISTS

        # Determine bit depth and codec
        codec = self.target_format.codec
        if self.preserve_bit_depth:
            actual_bit_depth = self.media.find_bit_depth(input_path)
            if actual_bit_depth in {24, 32}:
                self.bit_depth = actual_bit_depth
                codec = self.target_format.get_codec_for_bit_depth(self.bit_depth)

        with conversion_list_context(input_path.name):
            try:
                self.media.ffmpeg_audio(
                    input_files=input_path,
                    output_format=self.target_format.extension,
                    codec=codec,
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


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description=__doc__, lines=2)

    # Format selection group
    format_group = parser.add_argument_group("Formats")

    # Add options for each format
    for fmt_key, fmt in ALACrity.FORMATS.items():
        if fmt_key == "aif":  # Skip aliases, keep only one
            continue
        format_group.add_argument(
            f"--{fmt.extension}", action="store_true", help=f"Convert files to {fmt.name}"
        )

    # Special operation modes
    operation_group = parser.add_argument_group("Operations")
    operation_group.add_argument(
        "--undo",
        action="store_true",
        help=f"Convert {ALACrity.UNDO_SOURCE_EXTENSIONS[0].upper()} files back to "
        f"{ALACrity.UNDO_TARGET_FORMAT.name} (preserves bit depth)",
    )
    operation_group.add_argument(
        "--preserve-depth", action="store_true", help="Preserve bit depth if higher than 16-bit"
    )

    # Paths argument
    paths_help = "file(s) or directory of files to convert (defaults to current directory)"
    parser.add_argument("paths", nargs="*", default=[Path.cwd()], help=paths_help)

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()
    ALACrity(args)
