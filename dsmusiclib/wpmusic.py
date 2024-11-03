"""
Uploads and replaces Evanescence remixes on WordPress.

This is a sophisticated script to automate the process of converting and uploading my Evanescence
remixes to my WordPress site. With frequent updates and revisions, ensuring consistent quality along
with correct filenames, metadata, and cover art became a real chore, hence this script.

It takes an audio file as an argument and first identifies the song by comparing its normalized
filename against the file URLs in the JSON file that lists all my remixes on my site. This includes
whether the song is an instrumental version or not. It then converts the file to FLAC and ALAC, adds
the correct metadata and cover art for each format, and uploads the files to my web server.

When finished, it deletes the locally converted files, unless the `--keep-files` argument is
provided when running the script, in which case the files are renamed to match the track title. The
script also supports a `--skip-upload` argument that will convert but not upload. When
`--skip-upload` is used, local files are always kept (as if `--keep-files` was also used).
"""

from __future__ import annotations

import argparse
import os
import sys

from termcolor import colored

from dsmusiclib.wpmusiclib.audio_track import AudioTrack
from dsmusiclib.wpmusiclib.file_manager import FileManager
from dsmusiclib.wpmusiclib.metadata_setter import MetadataSetter
from dsmusiclib.wpmusiclib.track_identifier import TrackIdentifier
from dsmusiclib.wpmusiclib.upload_tracker import UploadTracker
from dsmusiclib.wpmusiclib.wp_config import Config, spinner
from dsutil.log import LocalLogger
from dsutil.media import ffmpeg_audio
from dsutil.shell import handle_keyboard_interrupt


class WPMusic:
    """Upload and replace Evanescence remixes on WordPress."""

    def __init__(self, command_args: list[str]):
        self.args = self.parse_arguments(command_args)

        if self.args.doc or not command_args:
            self.show_help_and_exit()

        self.skip_upload = self.args.skip_upload
        self.keep_files = self.args.keep_files or self.skip_upload  # Always keep if skipping upload
        self.debug = self.args.debug

        self.config = Config(
            skip_upload=self.skip_upload,
            keep_files=self.keep_files,
            debug=self.debug,
        )
        self.logger = LocalLogger.setup_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            message_only=True,
        )
        self.track_identifier = TrackIdentifier(self.config)
        self.metadata_setter = MetadataSetter(self.config)
        self.upload_tracker = UploadTracker(self.config)
        self.file_manager = FileManager(self.config, self.upload_tracker)

        self.main()

    @handle_keyboard_interrupt()
    def main(self) -> None:
        """Process and upload multiple audio files or display history."""
        if self.args.history is not None:
            self.display_history()
        elif self.args.files:
            for file_path in self.args.files:
                try:
                    self.process_file(file_path)
                except Exception as e:
                    self.logger.error("An error occurred processing %s: %s", file_path, str(e))
        else:
            self.logger.error("No input files specified and no --history argument. Nothing to do.")
            sys.exit(1)

    def display_history(self) -> None:
        """Display upload history."""
        track_name = self.args.history if self.args.history != "" else None
        if track_name:
            self.upload_tracker.pretty_print_history(track_name=track_name, limit=None)
        else:
            self.upload_tracker.pretty_print_history()

    def process_file(self, file_path: str) -> None:
        """Process a single audio file."""
        audio_track = AudioTrack(file_path, append_text=self.args.append)

        try:  # Identify track and set metadata
            track_metadata = self.track_identifier.identify_track(audio_track)
            audio_track.set_track_metadata(track_metadata)

            self.logger.info(
                "%s %s%s...",
                "Converting" if self.skip_upload else "Converting and uploading",
                audio_track.track_name,
                " (Instrumental)" if audio_track.is_instrumental else "",
            )

            if not audio_track.track_metadata:
                msg = "No track selected. Skipping this file."
                raise TypeError(msg)

            output_filename = self.file_manager.format_filename(audio_track)
            self.process_and_upload(audio_track, output_filename)

            if not self.config.skip_upload:
                self.file_manager.print_and_copy_urls(output_filename)

            if not self.keep_files:
                self.file_manager.cleanup_files_after_upload(audio_track, output_filename)

        except Exception as e:
            self.logger.error("An error occurred: %s", str(e))

    def process_and_upload(self, audio_track: AudioTrack, output_filename: str) -> None:
        """Convert the files, apply metadata, and upload them to the web server."""
        self.logger.debug("Adding metadata for '%s'...", audio_track.track_name)

        for format_name in self.config.formats_to_convert:
            # Convert the file to the desired format
            spinner.start(colored(f"Converting to {format_name.upper()}...", "cyan"))
            output_path = self.convert_file_to_format(
                audio_track.filename, format_name, output_filename
            )

            self.logger.debug("Converted to %s. File path: %s", format_name.upper(), output_path)

            # Add metadata to the converted file
            spinner.start(colored(f"Adding metadata to {format_name.upper()} file...", "cyan"))
            processed_file = self.metadata_setter.apply_metadata(
                audio_track, format_name, output_path
            )

            self.logger.debug("Processed file path: %s", processed_file)

            # Upload the file if it's in the list of formats to upload
            if format_name in self.config.formats_to_upload and not self.skip_upload:
                self.logger.debug("Uploading %s file...", format_name.upper())
                spinner.start(colored(f"Uploading {format_name.upper()} file...", "cyan"))
                self.file_manager.upload_file_to_web_server(processed_file, audio_track)

            spinner.succeed(colored(f"{format_name.upper()} processing complete!", "green"))

        # After all formats are uploaded
        self.upload_tracker.log_upload_set()

        if not self.skip_upload:
            spinner.succeed(colored("Upload complete!", "green"))
        else:
            spinner.succeed(colored("Conversion complete! Files kept locally.", "green"))

    def convert_file_to_format(self, input_file: str, format_name: str, base_filename: str) -> str:
        """Convert the input file to a different format."""
        format_ext = self.config.formats.get(format_name)

        if not format_ext:
            msg = f"Unsupported file format: {format_name}"
            raise ValueError(msg)

        output_file_path = os.path.join(self.config.save_path, f"{base_filename}{format_ext}")
        self.logger.debug("Output file path for %s: %s", format_name.upper(), output_file_path)

        ffmpeg_audio(
            input_files=input_file,
            output_format=format_ext[1:],
            output_file=output_file_path,
            overwrite=True,
            show_output=False,
        )

        return output_file_path

    def parse_arguments(self, args_list: list[str]) -> argparse.Namespace:
        """Parse command-line arguments from a given list."""
        parser = argparse.ArgumentParser(description="Convert and upload audio files to WordPress.")
        parser.add_argument(
            "--skip-upload",
            action="store_true",
            help="convert only, skip uploading (implies --keep-files)",
            default=False,
        )
        parser.add_argument(
            "--keep-files",
            action="store_true",
            help="keep converted files after upload",
            default=False,
        )
        parser.add_argument(
            "--append",
            help="append text to the song title",
            default="",
        )
        parser.add_argument(
            "--doc",
            action="store_true",
            help="show the full documentation and exit",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="show debug logging",
        )
        parser.add_argument(
            "--history",
            nargs="?",
            const="",
            help="display upload history, optionally filtered by track name",
        )

        # Parse known args first
        args, remaining = parser.parse_known_args(args_list)

        # Treat all remaining arguments as files
        args.files = remaining or []

        return args

    def show_help_and_exit(self) -> None:
        """Print the script's docstring and exit."""
        print(__doc__)
        sys.exit()
