from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import inquirer
import paramiko  # type: ignore
import pyperclip
from polykit.cli import handle_interrupt
from polykit.files import PolyFile
from polykit.formatters import color as colored
from polykit.log import PolyLog
from scp import SCPClient

if TYPE_CHECKING:
    from dsbin.wpmusic.audio_track import AudioTrack
    from dsbin.wpmusic.configs import WPConfig
    from dsbin.wpmusic.upload_tracker import UploadTracker


class WPFileManager:
    """Manage file operations."""

    def __init__(self, config: WPConfig, upload_tracker: UploadTracker):
        self.config = config
        self.upload_tracker = upload_tracker
        self.logger = PolyLog.get_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            simple=self.config.log_simple,
        )
        self.file_save_path = Path(self.config.file_save_path)

    def format_filename(self, audio_track: AudioTrack) -> str:
        """Format filename for the converted file based on the metadata and any appended text."""
        track_name = str(audio_track.track_name)  # Convert to string for string operations
        self.logger.debug("Filename derived from track name: '%s'", track_name)

        # Remove apostrophes and replace spaces and other non-alphanumeric characters with hyphens
        track_name = track_name.replace("'", "")  # Remove apostrophes first
        base_filename = re.sub(r"[^a-zA-Z0-9-]", "-", track_name).strip("-")
        self.logger.debug("Filename with hyphens instead of spaces: %s", base_filename)

        # Append '_Inst' if the track is an instrumental
        if audio_track.is_instrumental:
            base_filename += "_Inst"
            self.logger.debug("Filename for instrumental: %s", base_filename)

        # Construct output path
        output_path = self.file_save_path / f"{base_filename}.flac"
        self.logger.debug("Output filename: %s", output_path)

        if audio_track.append_text:
            try:
                base_filename = self.prompt_for_custom_filename(base_filename)
            except TypeError:
                self.logger.error("No filename provided. Aborting.")
                return ""

        return base_filename or ""

    @handle_interrupt()
    def prompt_for_custom_filename(self, default_filename: str) -> str | None:
        """Prompt the user to enter a custom filename."""
        questions = [
            inquirer.Text(
                "filename",
                message=colored("Enter custom filename", "yellow"),
                default=default_filename,
            )
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            return None

        self.logger.debug("Custom filename: %s", answers["filename"])
        return answers["filename"]

    def cleanup_files_after_upload(self, audio_track: AudioTrack, output_filename: str) -> None:
        """Clean up the files after upload.

        Args:
            audio_track: The AudioTrack object containing the track metadata.
            output_filename: The base filename for the converted files.
        """
        files_to_process = [  # List of files to process based on requested formats
            self.file_save_path / f"{output_filename}{self.config.formats[fmt]}"
            for fmt in self.config.formats_to_convert
        ]
        if self.config.keep_files:  # If keeping files, rename to match the song name
            song_name = audio_track.track_title
            for fmt in self.config.formats_to_convert:
                old_path = self.file_save_path / f"{output_filename}{self.config.formats[fmt]}"
                new_path = self.file_save_path / f"{song_name}{self.config.formats[fmt]}"
                if old_path.exists():
                    old_path.rename(new_path)
                else:
                    self.logger.warning("File not found for renaming: %s", old_path)

            self.logger.info("Local files kept and renamed to '%s'.", song_name)

        else:  # Otherwise, delete the files
            PolyFile.delete(files_to_process)

    def upload_file_to_web_server(self, file_path: Path, audio_track: AudioTrack) -> None:
        """Upload a file to my web server."""
        final_filename = file_path.name
        try:
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    self.config.ssh_host,
                    username=self.config.ssh_user,
                    pkey=self.config.private_key,
                )

                temp_filename = f"tmp-{final_filename}"
                self.logger.debug("Uploading file '%s' as '%s'...", file_path, temp_filename)

                with SCPClient(ssh.get_transport()) as scp:  # type: ignore
                    scp.put(str(file_path), f"{self.config.upload_path_prefix}{temp_filename}")

                # Rename the temporary file to the final filename on the remote server
                self.logger.debug("Renaming '%s' to '%s'...", temp_filename, final_filename)
                ssh_command = (
                    f"mv {self.config.upload_path_prefix}{temp_filename}"
                    f" {self.config.upload_path_prefix}{final_filename}"
                )
                _, stdout, _ = ssh.exec_command(ssh_command)
                if stdout.channel.recv_exit_status() != 0:
                    self.logger.error(
                        "An error occurred while renaming the file on the remote server."
                    )
                    return

                # Log the successful upload
                self.upload_tracker.current_upload_set[audio_track.track_name][str(file_path)] = (
                    audio_track
                )

        except Exception as e:
            self.logger.error("SSH error: %s", str(e))

    def print_and_copy_urls(self, base_filename: str, is_pair: bool = False) -> None:
        """Print the URLs of uploaded files and copy the FLAC URL to the clipboard."""
        flac_url = f"{self.config.upload_url_prefix}{base_filename}.flac"
        alac_url = f"{self.config.upload_url_prefix}{base_filename}.m4a"

        if not is_pair:
            pyperclip.copy(flac_url)

        print("\nURLs of uploaded files:")
        print(colored(flac_url, "blue"), end="")

        if not is_pair:
            print("  ← on clipboard")
        else:
            print()

        print(colored(alac_url, "blue"))

        if not is_pair:
            print()
