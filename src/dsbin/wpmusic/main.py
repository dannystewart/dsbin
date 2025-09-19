"""Uploads and replaces song remixes on WordPress.

This is a sophisticated script to automate the process of converting and uploading my song remixes
to my WordPress site. With frequent updates and revisions, ensuring consistent quality along with
correct filenames, metadata, and cover art became a real chore, hence this script.

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

import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from halo import Halo
from polykit import PolyArgs, PolyLog
from polykit.cli import handle_interrupt, walking_man
from polykit.core import polykit_setup
from polykit.text import color

from dsbin.media import MediaManager
from dsbin.wpmusic.configs import WPConfig
from dsbin.wpmusic.metadata_handler import MetadataHandler
from dsbin.wpmusic.track_identifier import TrackIdentifier
from dsbin.wpmusic.upload_tracker import UploadTracker
from dsbin.wpmusic.wp_file_manager import WPFileManager

if TYPE_CHECKING:
    import argparse

    from dsbin.wpmusic.audio_track import AudioTrack

polykit_setup()


class WPMusic:
    """Upload and replace song remixes on WordPress."""

    def __init__(self, args: argparse.Namespace):
        # Determine if we're skipping upload based on subcommand
        skip_upload = args.command == "convert"

        # Keep files based on argument or if converting (convert always keeps files)
        should_keep = getattr(args, "keep_files", False) or skip_upload

        # Initialize configuration and logger
        self.config = WPConfig(
            skip_upload=skip_upload,
            keep_files=should_keep,
            no_cache=args.no_cache,
        )
        self.logger = PolyLog.get_logger(level=self.config.log_level, simple=self.config.log_simple)
        self.args = args  # Store args for later processing
        self.spinner = Halo(text="Initializing", spinner="dots", color="cyan")

        # Check if we have a valid command
        if not args.command:
            self.logger.error(
                "No command specified. Use 'wpmusic --help' to see available commands."
            )
            sys.exit(1)

        # Only check for files if we're not doing history or DB operations
        if (
            args.command in {"upload", "convert"}
            and not getattr(args, "files", [])
            and not args.test_db_connection
            and not args.refresh_cache
        ):
            self.logger.error("No input files specified. Nothing to do.")
            sys.exit(1)

        # Initialize components
        self.metadata_handler = MetadataHandler(self.config, self.logger)
        self.track_identifier = TrackIdentifier(self.config, self.metadata_handler, self.logger)
        self.upload_tracker = UploadTracker(self.config)
        self.file_manager = WPFileManager(self.config, self.upload_tracker, self.logger)

        with walking_man(color="cyan"):
            # Check SSH connectivity before proceeding
            if not self.config.skip_upload and not self.file_manager.check_ssh_connectivity():
                self.logger.error("SSH check failed. You may need to authenticate your SSH key.")
                sys.exit(1)

            # Check database connection if requested
            if self.args.test_db_connection:
                self.upload_tracker.db.check_database()

            # Force refresh of local cache if requested
            if self.upload_tracker.db.force_db_refresh(
                force_refresh=self.args.refresh_cache,
                refresh_only=not (
                    self.args.command == "history" or getattr(self.args, "files", [])
                ),
            ):
                return

        # Ensure Walking Man stops before proceeding (we thank him for his service)
        time.sleep(0.1)

        # Process files
        self.process()

    @handle_interrupt()
    def process(self) -> None:
        """Process and upload multiple audio files or display history."""
        if self.args.refresh_cache:
            self.logger.info("Forcing cache refresh from MySQL server...")
            self.upload_tracker.db.force_refresh()
            self.logger.info("Cache refresh complete!")
            if self.args.command != "history" and not getattr(self.args, "files", []):
                return

        if self.args.command == "history":
            self.display_history()
        elif self.args.command in {"upload", "convert"}:
            for file_path in self.args.files:
                try:
                    self.process_file(file_path)
                except Exception as e:
                    self.logger.error("An error occurred processing %s: %s", file_path, str(e))
        else:
            self.logger.error("Unknown command: %s", self.args.command)
            sys.exit(1)

    def display_history(self) -> None:
        """Display upload history."""
        track_name = getattr(self.args, "track_name", None)
        self.upload_tracker.pretty_print_history(
            track_name, uploads_per_song=getattr(self.args, "uploads_per_track", None)
        )

    def process_file(self, file_path: Path) -> None:
        """Process a single audio file and its potential instrumental pair."""
        # Process the original file first
        file_path = Path(file_path)
        track_metadata = self._process_single_file(file_path)

        # Check for and process matching instrumental file
        instrumental_path = self._find_instrumental_pair(file_path)
        if instrumental_path:
            print()
            self.logger.info("Found matching instrumental file: %s", instrumental_path)
            self._process_single_file(
                instrumental_path, is_pair=True, track_metadata=track_metadata
            )

    def _process_single_file(
        self,
        file_path: Path,
        is_pair: bool = False,
        track_metadata: dict[str, AudioTrack] | None = None,
    ) -> dict[str, AudioTrack]:
        """Process a single audio file.

        Args:
            file_path: Path to the audio file.
            is_pair: Whether this is part of an instrumental pair.
            track_metadata: Metadata of the original track, if already identified as part of a pair.

        Raises:
            TypeError: If no track is selected from the fallback menu.
            ValueError: If processing fails for any reason.
        """
        try:
            append_text = getattr(self.args, "append", "") or ""
            if not track_metadata:  # Identify the original track
                audio_track = self.track_identifier.create_audio_track(
                    file_path, append_text=append_text, spinner=self.spinner
                )
                track_metadata = audio_track.track_metadata
            else:  # If we already have metadata, it's the instrumental for the original track
                audio_track = self.track_identifier.create_audio_track(
                    file_path,
                    append_text=append_text,
                    is_instrumental=True,
                    track_metadata=track_metadata,
                )

            print()
            self.logger.info(
                "%s %s%s...",
                "Converting" if self.config.skip_upload else "Converting and uploading",
                audio_track.track_name,
                " (Instrumental)" if audio_track.is_instrumental else "",
            )

            if not audio_track.track_metadata:
                msg = "No track selected. Skipping this file."
                raise TypeError(msg)

            output_filename = self.file_manager.format_filename(audio_track)
            if not output_filename:
                self.spinner.stop()
                msg = "No output filename provided."
                raise ValueError(msg)

            self.process_and_upload(audio_track, output_filename)

            if not self.config.skip_upload:
                self.file_manager.print_and_copy_urls(output_filename, is_pair)

            if not self.config.keep_files:
                self.file_manager.cleanup_files_after_upload(audio_track, output_filename)

            if not track_metadata:
                msg = "Track metadata is unexpectedly None"
                raise ValueError(msg)

            return track_metadata

        except TypeError as e:
            self.logger.error("Process aborted by user: %s", str(e))
            raise
        except ValueError as e:
            self.logger.error("Processing failed: %s", str(e))
            raise

    def _find_instrumental_pair(self, file_path: Path) -> Path | None:
        """Find a matching instrumental file for the given file path."""
        base_path = file_path.stem
        ext = file_path.suffix

        # Skip if this is already an instrumental file
        if base_path.endswith(" No Vocals"):
            return None

        # Check for instrumental pair
        instrumental_path = file_path.with_name(f"{base_path} No Vocals{ext}")
        return instrumental_path if instrumental_path.exists() else None

    def process_and_upload(self, audio_track: AudioTrack, output_filename: str) -> None:
        """Convert the files, apply metadata, and upload them to the web server."""
        self.logger.debug("Adding metadata for '%s'...", audio_track.track_name)

        for format_name in self.config.formats_to_convert:
            # Convert the file to the desired format
            self.spinner.start(color(f"Converting to {format_name.upper()}...", "cyan"))
            output_path = self.convert_file_to_format(
                audio_track.filename, format_name, output_filename
            )

            self.logger.debug("Converted to %s. File path: %s", format_name.upper(), output_path)

            # Add metadata to the converted file
            self.spinner.start(color(f"Adding metadata to {format_name.upper()} file...", "cyan"))
            processed_file = self.metadata_handler.apply_metadata(
                audio_track, format_name, output_path
            )

            self.logger.debug("Processed file path: %s", processed_file)

            # Upload the file if it's in the list of formats to upload
            if format_name in self.config.formats_to_upload and not self.config.skip_upload:
                self.logger.debug("Uploading %s file...", format_name.upper())
                # Stop spinner before upload to avoid interfering with progress bar
                self.spinner.stop()
                self.file_manager.upload_file_to_web_server(processed_file, audio_track)

            self.spinner.succeed(color(f"{format_name.upper()} processing complete!", "green"))

        # Only record to the database if this is a known track with full metadata
        if audio_track.metadata_skipped:
            self.logger.debug(
                "Not recording '%s' to the database as it was not matched with a known track.",
                audio_track.track_name,
            )
            self.upload_tracker.current_upload_set.clear()
        else:
            self.upload_tracker.log_upload_set()

        if not self.config.skip_upload:
            self.spinner.succeed(color("Upload complete!", "green"))
        else:
            self.spinner.succeed(color("Conversion complete! Files kept locally.", "green"))

    def convert_file_to_format(self, input_file: str, format_name: str, base_filename: str) -> Path:
        """Convert the input file to a different format.

        Raises:
            ValueError: If the file format is not supported.
        """
        format_ext = self.config.formats.get(format_name)

        if not format_ext:
            msg = f"Unsupported file format: {format_name}"
            raise ValueError(msg)

        output_file_path = Path(self.config.file_save_path) / f"{base_filename}{format_ext}"
        self.logger.debug("Output file path for %s: %s", format_name.upper(), output_file_path)

        MediaManager().ffmpeg_audio(
            input_files=Path(input_file),
            output_format=format_ext[1:],  # Remove the leading dot
            output_filename=str(output_file_path),
            overwrite=True,
            show_output=False,
        )

        return output_file_path

    @staticmethod
    def show_help_and_exit() -> None:
        """Print the script's docstring and exit."""
        print(__doc__)
        sys.exit()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    description = "Convert and upload audio files to WordPress, or display upload history."
    parser = PolyArgs(description=description, arg_width=28)
    subparsers = parser.add_subparsers(dest="command", help="available commands")

    # Upload subcommand
    upload_parser = subparsers.add_parser("upload", help="convert and upload files")
    upload_parser.add_argument("files", nargs="+", help="audio files to upload")
    upload_parser.add_argument(
        "--keep-files", action="store_true", help="keep converted files after upload", default=False
    )
    upload_parser.add_argument("--append", help="append text to the song title", default="")

    # Convert subcommand
    convert_parser = subparsers.add_parser("convert", help="convert files without uploading")
    convert_parser.add_argument("files", nargs="+", help="audio files to convert")
    convert_parser.add_argument("--append", help="append text to the song title", default="")

    # History subcommand
    history_parser = subparsers.add_parser("history", help="show upload history by track")
    history_parser.add_argument(
        "track_name", nargs="?", help="optional track name to filter history"
    )
    history_parser.add_argument(
        "-u", "--uploads-per-track", type=int, help="uploads to show per track (default: 3)"
    )
    history_parser.add_argument(
        "--no-cache", action="store_true", help="bypass local cache and use MySQL server directly"
    )
    history_parser.add_argument(
        "--refresh-cache", action="store_true", help="refresh local cache from MySQL server"
    )
    history_parser.add_argument(
        "--test-db-connection", action="store_true", help="test database connection and exit"
    )
    return parser.parse_args()


def main() -> None:
    """Process and upload audio files to WordPress."""
    args = parse_arguments()
    WPMusic(args)


if __name__ == "__main__":
    main()
