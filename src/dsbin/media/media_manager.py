from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.cli import conditional_walking_man, halo_progress
from polykit.log import Logician

if TYPE_CHECKING:
    from logging import Logger


class MediaManager:
    """A utility class with a comprehensive set of methods for common media operations."""

    def __init__(
        self,
        log_level: str = "info",
        detailed_log: bool = False,
        logger: Logger | None = None,
    ):
        self.logger: Logger = logger or Logician.get_logger(
            level=log_level, simple=not detailed_log
        )

    def run_ffmpeg(
        self,
        command: list[str],
        input_file: Path,
        show_output: bool,
        output_filename: str | None = None,
    ) -> None:
        """Run a given ffmpeg command and handle progress display and errors.

        Args:
            command: The ffmpeg command to execute.
            input_file: The path to the input file.
            show_output: Whether to display output.
            output_filename: The name of the output file to show when converting. Defaults to None,
                in which case the input filename is used instead.

        Raises:
            RuntimeError: If the ffmpeg command fails.
        """
        with halo_progress(
            output_filename or input_file.name,
            start_message="Converting",
            end_message="Converted",
            fail_message="Failed to convert",
            show=show_output,
        ) as spinner:
            try:
                subprocess.run(command, check=True, stderr=subprocess.PIPE, text=True)

            except subprocess.CalledProcessError as e:
                spinner.fail()
                self.logger.error("Error running command '%s': %s", command, str(e.stderr))
                raise RuntimeError from e

            except Exception as e:
                spinner.fail()
                self.logger.error("Unexpected error converting file '%s': %s", input_file, str(e))
                raise

    def ffmpeg_audio(
        self,
        input_files: Path | list[Path],
        output_format: str,
        output_filename: str | None = None,
        overwrite: bool = True,
        codec: str | None = None,
        bit_depth: int | None = None,
        audio_bitrate: str | None = None,
        sample_rate: str | None = None,
        preserve_metadata: bool = False,
        additional_args: list[str] | None = None,
        show_output: bool = False,
        show_animation: bool = False,
    ) -> None:
        """Convert an audio file to a different format using ffmpeg with various options.
        Automatically prioritizes lossless formats over lossy formats.

        Args:
            input_files: The path to the input file or a list of paths to input files.
            output_format: The desired output format.
            output_filename: The output filename. Defaults to None, which uses the input filename.
            overwrite: Whether to overwrite the output file if it already exists. Defaults to True.
            codec: The desired codec. Defaults to None.
            bit_depth: The desired bit depth. Defaults to 16.
            audio_bitrate: The desired audio bitrate. Defaults to None.
            sample_rate: The desired sample rate. Defaults to None.
            preserve_metadata: Whether to preserve existing metadata. Defaults to False.
            additional_args: List of additional arguments to pass to ffmpeg. Defaults to None.
            show_output: Whether to display ffmpeg output. Defaults to False.
            show_animation: Whether to show the loading animation. Defaults to False.
        """
        if not isinstance(input_files, list):
            input_files = [input_files]

        input_files = self.ensure_lossless_first(input_files)

        for input_file in input_files:
            current_bit_depth = bit_depth or self.find_bit_depth(
                input_file, show_animation=show_animation
            )

            current_output_file = self.construct_filename(
                input_file,
                output_filename,
                output_format,
                input_files,
            )
            command = self.construct_ffmpeg_command(input_file, overwrite)

            self.add_audio_flags(
                command,
                codec,
                output_format,
                audio_bitrate,
                sample_rate,
                current_bit_depth,
                preserve_metadata,
                input_file,
            )

            if additional_args:
                command.extend(additional_args)

            command.append(current_output_file)
            self.run_ffmpeg(command, input_file, show_output, current_output_file)

    def add_audio_flags(
        self,
        command: list[str],
        codec: str | None,
        output_format: str,
        audio_bitrate: str | None = None,
        sample_rate: str | None = None,
        bit_depth: int | None = None,
        preserve_metadata: bool = False,
        input_file: Path | None = None,
    ) -> None:
        """Add the necessary flags for the desired audio codec settings to the ffmpeg command.

        Args:
            command: The ffmpeg command to which to apply the settings.
            codec: The desired codec. Defaults to None.
            output_format: The desired output format.
            audio_bitrate: The desired audio bitrate. Defaults to None.
            sample_rate: The desired sample rate. Defaults to None.
            bit_depth: The desired bit depth. Defaults to None.
            preserve_metadata: Whether to preserve existing metadata. Defaults to False.
            input_file: The path to the input file. Needed to check video streams. Defaults to None.
        """
        if output_format == "m4a" and not codec:
            codec = "alac"

        if preserve_metadata:
            command.extend(["-map_metadata", "0"])
            if input_file and self.has_video_stream(input_file):
                command.extend(["-map", "0:v", "-c:v", "copy"])
            command.extend(["-map", "0:a"])
        else:
            command.append("-vn")

        if codec:
            command += ["-acodec", codec]
        else:
            codec_to_format = {
                "mp3": "libmp3lame",
                "wav": "pcm_s16le",
                "flac": "flac",
                "m4a": "alac",  # Default to ALAC for m4a
            }
            command += ["-acodec", codec_to_format.get(output_format, "copy")]

        if audio_bitrate:
            command += ["-b:a", audio_bitrate]

        if sample_rate:
            command += ["-ar", sample_rate]

        command.extend(self._get_arguments_for_codec(output_format, bit_depth))

    def find_bit_depth(self, input_file: Path, show_animation: bool = False) -> int:
        """Identify the bit depth of an input audio file using ffprobe.
        Returns the bit depth of the input file, or 0 if the bit depth could not be determined.

        Args:
            input_file: The path to the input file.
            show_animation: Whether to show the loading animation. Defaults to False.
        """
        with conditional_walking_man(show_animation):
            bit_depth_command = (  # First, try to get the bit depth in the usual way
                f"ffprobe -v error -select_streams a:0 -show_entries stream=bits_per_raw_sample "
                f'-of default=noprint_wrappers=1:nokey=1 "{input_file}"'
            )
            bit_depth = subprocess.getoutput(bit_depth_command)
            if bit_depth.isdigit():
                self.logger.debug("Found bit depth %s for %s.", bit_depth, input_file)
                return int(bit_depth)

            codec_command = (  # If that fails, try to extract the audio codec format
                f"ffprobe -v error -select_streams a:0 -show_entries stream=codec_name "
                f'-of default=noprint_wrappers=1:nokey=1 "{input_file}"'
            )
            codec = subprocess.getoutput(codec_command)
            if "pcm_s16" in codec:
                self.logger.debug("Determined 16-bit depth from codec '%s'.", codec)
                return 16
            if "pcm_s24" in codec:
                self.logger.debug("Determined 24-bit depth from codec '%s'.", codec)
                return 24
            if "pcm_s32" in codec:
                self.logger.debug("Determined 32-bit depth from codec '%s'.", codec)
                return 32

        self.logger.warning("Bit depth could not be determined. Skipping 24-bit conversion.")
        return 0

    @staticmethod
    def construct_filename(
        input_file: Path,
        output_filename: str | None,
        output_format: str | None,
        input_files: list[Path],
    ) -> str:
        """Construct the output filename based on the input file and the output format.

        Args:
            input_file: The path to the input file.
            output_filename: The path to the output file. Defaults to None.
            output_format: The desired output format.
            input_files: A list of input files.
        """
        if not output_filename:
            return f"{input_file.stem}.{output_format}"

        final_output = (
            output_filename
            if len(input_files) == 1
            else f"{Path(output_filename).stem}_{input_file.name}{Path(output_filename).suffix}"
        )
        return str(final_output)

    @staticmethod
    def construct_ffmpeg_command(input_file: Path, overwrite: bool) -> list[str]:
        """Construct the base ffmpeg command.

        Args:
            input_file: The path to the input file.
            overwrite: Whether to overwrite the output file if it already exists.
        """
        command = ["ffmpeg"]
        if overwrite:
            command += ["-y"]
        command += [
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(input_file),
        ]
        return command

    @staticmethod
    def _get_arguments_for_codec(output_format: str, bit_depth: int | None) -> list[str]:
        """Get the additional arguments needed specifically for the output format and bit depth."""
        command = []
        if output_format == "flac":
            command += ["-compression_level", "12"]
            command += ["-sample_fmt", "s16"]
        elif output_format == "m4a":
            if bit_depth:
                command += ["-bits_per_raw_sample", str(bit_depth)]
        elif output_format in {"wav", "aif", "aiff"}:
            if bit_depth in {16, 24, 32}:
                sample_format_mappings = {
                    16: "s16",
                    24: "s24",
                    32: "s32",
                }
                sample_format = sample_format_mappings.get(bit_depth, "s16")
                command += ["-sample_fmt", sample_format]
        return command

    @staticmethod
    def ensure_lossless_first(input_files: list[Path]) -> list[Path]:
        """If there are multiple files with the same name, this function will sort the list such
        that uncompressed and lossless files are prioritized over compressed and lossy files.
        """
        file_groups = defaultdict(list)

        for file in input_files:
            base_name = file.stem
            file_groups[base_name].append(file)

        prioritized_extensions = [".wav", ".aiff", ".aif", ".flac", ".m4a"]

        prioritized_files = []
        for files in file_groups.values():
            selected_file = None
            for ext in prioritized_extensions:
                for file in files:
                    if file.suffix.lower() == ext:
                        selected_file = file
                        break
                if selected_file:
                    break
            if not selected_file:
                selected_file = files[0]
            prioritized_files.append(selected_file)
        return prioritized_files

    def ffmpeg_video(
        self,
        input_files: Path | list[Path],
        output_format: str,
        output_file: str | None = None,
        overwrite: bool = True,
        video_codec: str | None = None,
        video_bitrate: str | None = None,
        audio_codec: str | None = None,
        additional_args: list[str] | None = None,
        show_output: bool = False,
    ):
        """Convert a video file to a different format using ffmpeg with various options.

        Args:
            input_files: The path to the input file or a list of paths to input files.
            output_format: The desired output format.
            output_file: The path to the output file. Defaults to None.
            overwrite: Whether to overwrite the output file if it already exists. Defaults to True.
            video_codec: The desired video codec. Defaults to None, which uses "copy".
            video_bitrate: The desired video bitrate. Defaults to None.
            audio_codec: The desired audio codec. Defaults to None, which uses "copy".
            additional_args: List of additional arguments to pass to ffmpeg. Defaults to None.
            show_output: Whether to display ffmpeg output. Defaults to False.
        """
        if not isinstance(input_files, list):
            input_files = [input_files]

        for input_file in input_files:
            current_output_file = self.construct_filename(
                input_file,
                output_file,
                output_format,
                input_files,
            )
            command = self.construct_ffmpeg_command(input_file, overwrite)
            self.add_video_flags(command, video_codec, video_bitrate, audio_codec)

            if additional_args:
                command.extend(additional_args)

            command.append(current_output_file)
            self.run_ffmpeg(command, input_file, show_output)

    def has_video_stream(self, file_path: Path) -> bool:
        """Check if the file has a video stream (potentially cover art)."""
        stream_info = self.get_stream_info(file_path)
        return any(stream["codec_type"] == "video" for stream in stream_info["streams"])

    @staticmethod
    def add_video_flags(
        command: list[str],
        video_codec: str | None,
        video_bitrate: str | None,
        audio_codec: str | None,
    ) -> None:
        """Add the necessary flags for the desired video codec settings to the ffmpeg command.

        Args:
            command: The ffmpeg command to which to apply the settings.
            video_codec: The desired video codec. Defaults to None.
            video_bitrate: The desired video bitrate. Defaults to None.
            audio_codec: The desired audio codec. Defaults to None.
        """
        command += ["-c:v", video_codec] if video_codec else ["-c:v", "copy"]
        if video_bitrate:
            command += ["-b:v", video_bitrate]

        command += ["-c:a", audio_codec] if audio_codec else ["-c:a", "copy"]

    @staticmethod
    def get_stream_info(file_path: Path) -> dict[str, dict[dict[str, str], str]]:
        """Get stream information from the input file."""
        command = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", file_path]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return json.loads(result.stdout)
