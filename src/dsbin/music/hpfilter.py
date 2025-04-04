"""Apply a highpass filter to cut bass frequencies for HomePod playback.

This script is designed to make it easier for me to apply a highpass filter to audio files
so I can play them on my HomePods without worrying about the bass being too loud.

It can be used to process individual files or directories of files, and it accepts optional
arguments to change the cutoff or apply cover art to the converted files.

You can modify the default cutoff frequency and suffix for the album and folder names by
changing the DEFAULT_CUTOFF_FREQ and SUFFIX variables at the top of the script, or by
using the --cutoff argument to override the default cutoff for a single run.

The script will output to the 'HomePod' folder in the same directory as the input file by default.
This can be overridden with the `--output` argument.

Usage:
    hpfilter.py [-h] [--cover COVER_IMAGE][--cutoff CUTOFF_FREQ] [--output OUTPUT_FOLDER]
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import scipy.io.wavfile
from halo import Halo
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from polykit import polykit_setup
from polykit.parsers import color, print_color

if TYPE_CHECKING:
    from collections.abc import Callable

type NPArray = np.ndarray[Any, Any]

warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=scipy.io.wavfile.WavFileWarning)

polykit_setup()


# Default cutoff frequency if not specified
DEFAULT_CUTOFF_FREQ = 100

# Default suffix for folder and album name
SUFFIX = "HomePod"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for applying a highpass filter to audio files."""
    parser = argparse.ArgumentParser(
        description="Apply a highpass filter to reduce bass for HomePod."
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Input audio file(s) pattern, e.g., *.m4a",
    )
    parser.add_argument(
        "--cover",
        help="Path to cover art image to apply to files",
        metavar="COVER_IMAGE",
    )
    parser.add_argument(
        "--cutoff",
        type=int,
        default=DEFAULT_CUTOFF_FREQ,
        help="Cutoff frequency for highpass filter",
        metavar="CUTOFF_FREQ",
    )
    parser.add_argument(
        "--output",
        help="Output folder where processed files will be saved",
        metavar="OUTPUT_FOLDER",
    )
    return parser.parse_args()


def run_with_spinner(
    text: str, func: Callable[..., Any], *args: Any, **kwargs: Any
) -> Callable[..., Any]:
    """Run a function with a spinner animation to indicate progress.

    Args:
        text: The text to display before the spinner.
        func: The function to run.
        *args: The positional arguments to pass to the function.
        **kwargs: The keyword arguments to pass to the function.

    Returns:
        The result of the function.
    """
    spinner = Halo(text=text, spinner="dots")
    spinner.start()

    try:
        result = func(*args, **kwargs)
        spinner.succeed(color(f"Saved {Path(result).name}", "green"))
        return result
    except Exception as e:
        spinner.fail(color(f"Error: {e}", "red"))
        raise e
    finally:
        spinner.stop()


def read_audio_file(filepath: Path | str) -> tuple[NPArray, int]:
    """Read an audio file from the given filepath and return the audio data and sample rate.

    Args:
        filepath: The path to the audio file.

    Returns:
        The audio data and sample rate.

    Raises:
        ValueError: If the file extension is not supported.
    """
    filepath = Path(filepath)
    if filepath.is_dir():
        msg = f"The path '{filepath}' is a directory, not a file."
        raise ValueError(msg)

    extension = filepath.suffix.lower()

    if extension == ".wav":
        sample_rate, data = scipy.io.wavfile.read(str(filepath))
        # Convert to float32 and normalize
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32767.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483647.0
        return data, sample_rate

    if extension in {".flac", ".m4a"}:
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_wav:
            # Convert to WAV using ffmpeg
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(filepath),
                "-f",
                "wav",
                "-c:a",
                "pcm_s16le",
                temp_wav.name,
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            # Read the WAV file
            sample_rate, data = scipy.io.wavfile.read(temp_wav.name)
            data = data.astype(np.float32) / 32767.0
            return data, sample_rate

    msg = f"Unsupported file format: {extension}"
    raise ValueError(msg)


def write_audio_file(
    filepath: Path | str,
    data: NPArray,
    sample_rate: int,
    original_file: Path | str,
    cover_art: Path | str | None,
) -> None:
    """Write audio data to a file with the specified filepath, sample rate, and number of channels.

    The original file is used to copy metadata to the new file.

    Args:
        filepath: The path to the output file.
        data: The audio data.
        sample_rate: The sample rate of the audio data.
        original_file: The path to the original file.
        cover_art: The path to the cover art image.

    Raises:
        ValueError: If the file extension is not supported.
    """
    filepath = Path(filepath)
    extension = filepath.suffix.lower()

    # Convert float32 to int16
    data_int = (data * 32767).astype(np.int16)

    if extension == ".wav":
        scipy.io.wavfile.write(str(filepath), sample_rate, data_int)
    elif extension in {".flac", ".m4a"}:
        # Write to temporary WAV first
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_wav:
            scipy.io.wavfile.write(temp_wav.name, sample_rate, data_int)

            # Convert to final format using ffmpeg
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                temp_wav.name,
            ]

            if extension == ".flac":
                cmd.extend(["-c:a", "flac"])
            else:  # .m4a
                cmd.extend(["-c:a", "alac"])

            cmd.append(str(filepath))

            subprocess.run(cmd, capture_output=True, check=True)
    else:
        msg = f"Unsupported file format: {extension}"
        raise ValueError(msg)

    copy_metadata(original_file, filepath, cover_art)


def copy_metadata(src: Path | str, dst: Path | str, cover_art: Path | str | None) -> None:
    """Copy the metadata from the source file to the destination file with cover art.

    Args:
        src: The path to the source file.
        dst: The path to the destination file.
        cover_art: The path to the cover art image.
    """
    src, dst = Path(src), Path(dst)
    src_extension = src.suffix.lower()
    src_meta: FLAC | MP4
    dst_meta: FLAC | MP4

    if src_extension == ".flac":
        src_meta = FLAC(str(src))
        dst_meta = FLAC(str(dst))

        if cover_art:
            with Path(cover_art).open("rb") as img_file:
                dst_meta.clear_pictures()
                picture = Picture()
                picture.data = img_file.read()
                dst_meta.add_picture(picture)

        elif src_meta.pictures:
            dst_meta.clear_pictures()
            for pic in src_meta.pictures:
                dst_meta.add_picture(pic)

        if "album" in src_meta:
            dst_meta["album"] = src_meta["album"][0] + f" ({SUFFIX})"

        dst_meta.save()

    elif src_extension == ".m4a":
        src_meta = MP4(str(src))
        dst_meta = MP4(str(dst))

        if cover_art:
            with Path(cover_art).open("rb") as img_file:
                dst_meta["covr"] = [MP4Cover(img_file.read(), MP4Cover.FORMAT_JPEG)]

        elif "covr" in src_meta:
            dst_meta["covr"] = src_meta["covr"]

        if "©alb" in src_meta:
            dst_meta["©alb"] = src_meta["©alb"][0] + f" ({SUFFIX})"
        else:
            dst_meta["©alb"] = f"Unknown Album ({SUFFIX})"

        dst_meta.save()


def process_m4a_with_ffmpeg(
    input_filepath: Path | str,
    output_directory: Path | str,
    cutoff_freq: int,
    cover_art: Path | str | None,
) -> Callable[[str, Callable[[], str]], str]:
    """Process an M4A audio file using ffmpeg.

    Args:
        input_filepath: The path to the input file.
        output_directory: The path to the output directory.
        cutoff_freq: The cutoff frequency for the highpass filter.
        cover_art: The path to the cover art image.

    Returns:
        The path to the output file.
    """
    input_filepath = Path(input_filepath)
    output_directory = Path(output_directory)
    output_filepath = output_directory / input_filepath.name
    output_directory.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_filepath),
        "-map",
        "0:a",
        "-af",
        f"highpass=f={cutoff_freq},volume=-3dB",
        "-c:a",
        "alac",
        "-map",
        "0:v?",
        "-c:v",
        "copy",
        str(output_filepath),
    ]

    def run_command() -> str:
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        output_filepath_updated = output_directory / input_filepath.name
        copy_metadata(input_filepath, output_filepath_updated, cover_art)
        return str(output_filepath_updated)

    return run_with_spinner(color(f"Processing {input_filepath.name}...", "cyan"), run_command)


def highpass_filter(data: NPArray, cutoff_freq: int, sample_rate: int) -> NPArray:
    """Apply a highpass filter to the input data.

    Args:
        data: The audio data.
        cutoff_freq: The cutoff frequency for the highpass filter.
        sample_rate: The sample rate of the audio data.

    Returns:
        The filtered audio data.
    """
    b, a = scipy.signal.butter(1, cutoff_freq / (0.5 * sample_rate), btype="high", analog=False)
    return scipy.signal.lfilter(b, a, data)


def process_file(
    input_filepath: Path | str,
    output_directory: Path | str,
    cutoff_freq: int,
    cover_art: Path | str | None,
) -> Callable[[str, Callable[[], str]], str]:
    """Process an input file by applying a cutoff frequency to filter the audio data.

    If the file extension is '.m4a', use the process_m4a_with_ffmpeg function to process the file
    and save it to the output directory. Then, copy the metadata from the input file to the output
    file and add a cover art if provided.

    Args:
        input_filepath: The path to the input file.
        output_directory: The path to the output directory.
        cutoff_freq: The cutoff frequency for the highpass filter.
        cover_art: The path to the cover art image.

    Returns:
        The spinner function that runs the operation.
    """
    input_filepath = Path(input_filepath)
    output_directory = Path(output_directory)
    extension = input_filepath.suffix.lower()

    if extension == ".m4a":
        return process_m4a_with_ffmpeg(input_filepath, output_directory, cutoff_freq, cover_art)

    def process() -> str:
        data, sample_rate = read_audio_file(input_filepath)
        channels = 2 if len(data.shape) > 1 else 1

        if channels == 1:
            filtered_data = highpass_filter(data, cutoff_freq, sample_rate)
        else:
            filtered_data = np.apply_along_axis(highpass_filter, 0, data, cutoff_freq, sample_rate)

        output_directory.mkdir(parents=True, exist_ok=True)
        basename = input_filepath.stem
        filename_with_suffix = f"{basename} {SUFFIX}{extension}"
        output_filepath = output_directory / filename_with_suffix

        write_audio_file(
            output_filepath,
            filtered_data.astype(np.float32),
            sample_rate,
            input_filepath,
            cover_art,
        )
        return str(output_filepath)

    return run_with_spinner(color(f"Processing {input_filepath}...", "cyan"), process)


def process_all_files(
    input_patterns: list[str],
    cutoff_freq: int,
    cover_art: Path | str | None,
    output_folder: Path | str | None = None,
) -> None:
    """Process all files that match the given input patterns.

    Each will be processed with the specified cutoff frequency and cover art.

    Args:
        input_patterns: A list of input file patterns.
        cutoff_freq: The cutoff frequency for the highpass filter.
        cover_art: The path to the cover art image.
        output_folder: The path to the output folder.
    """
    for input_pattern in input_patterns:
        input_path = Path(input_pattern)
        if input_path.is_dir() and "*" not in str(input_pattern):
            suggestion = str(input_path / "*")
            print_color(
                f"Warning: '{input_pattern}' is a directory. To process all files in this directory, use '{suggestion}' instead.",
                "yellow",
            )
            continue

        files = sorted(input_path.parent.glob(input_path.name))

        if not files:
            print(f"No files match the pattern {input_pattern}.")
            continue

        first_file = Path(files[0])
        output_directory = Path(output_folder) if output_folder else first_file.parent / SUFFIX
        output_directory.mkdir(parents=True, exist_ok=True)

        for filepath in files:
            filepath = Path(filepath)
            if filepath.is_dir():
                print(f"Skipping directory: {filepath}")
                continue
            try:
                process_file(filepath, output_directory, cutoff_freq, cover_art)
            except ValueError as e:
                print(f"Error processing file {filepath}: {e!s}")
                print(f"File exists: {filepath.exists()}")
                print(f"File size: {filepath.stat().st_size} bytes")
                continue


def main() -> None:
    """Parse arguments then process input files at specified cutoff frequency with cover art."""
    args = parse_arguments()

    process_all_files(
        args.input, cutoff_freq=args.cutoff, cover_art=args.cover, output_folder=args.output
    )
