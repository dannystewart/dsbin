from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, Any

import inquirer
from termcolor import colored

from .wp_config import Config, spinner

from dsutil.log import LocalLogger

if TYPE_CHECKING:
    from .audio_track import AudioTrack


class TrackIdentifier:
    """Identify a track based on input file and metadata."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = LocalLogger.setup_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            message_only=True,
        )

    def identify_track(self, audio_track: AudioTrack) -> dict:
        """Fetch track metadata based on the input file."""
        spinner.start(colored("Fetching track metadata...", "cyan"))

        try:
            return self._identify_by_name(audio_track)
        except ValueError:
            spinner.stop()
            try:
                return self._identify_by_fallback_menu(audio_track)
            except TypeError as e:
                msg = "No track selected. Aborting."
                raise TypeError(msg) from e

    def _identify_by_name(self, audio_track: AudioTrack) -> dict:
        """Identify the track by matching its upload filename against URLs in metadata."""
        self.logger.debug("Matching filename '%s' to track metadata...", audio_track.filename)

        # Remove "No Vocals" and strip the filename for comparison
        formatted_file_name = os.path.splitext(
            os.path.basename(audio_track.filename.replace(" No Vocals", "").replace("'", ""))
        )[0]
        formatted_file_name = re.sub(
            r" [0-9]+\.[0-9]+\.[0-9]+([._][0-9]+)?[a-z]*", "", formatted_file_name
        )
        formatted_file_name = re.sub(r"[^a-zA-Z0-9-]", "-", formatted_file_name).strip("-").lower()

        # Iterate through the tracks in the metadata and match the filename
        for track in audio_track.tracks:
            json_filename = (
                re.sub(
                    r"[^a-zA-Z0-9-]",
                    "-",
                    os.path.splitext(os.path.basename(track["file_url"].replace("'", "")))[0],
                )
                .strip("-")
                .lower()
            )
            self.logger.debug("Comparing '%s' with '%s'", formatted_file_name, json_filename)
            if formatted_file_name == json_filename:
                spinner.stop()
                self.logger.debug(
                    "Processing and uploading %s: %s", audio_track.filename, track["track_name"]
                )
                return track

        spinner.stop()
        msg = "No track found in metadata."
        raise ValueError(msg)

    def _identify_by_fallback_menu(self, audio_track: AudioTrack) -> dict:
        """Given track data, display a menu to select a track and retrieve its metadata."""
        self.logger.debug("No track found for filename '%s'.", audio_track.filename)

        selected_track_name = self._get_fallback_selection(audio_track.tracks)

        if selected_track_name == "(skip adding metadata)":
            return self._handle_skipped_metadata(audio_track)

        spinner.start()

        for track in audio_track.tracks:
            if track["track_name"] == selected_track_name:
                if audio_track.is_instrumental:
                    track["track_name"] += " (Instrumental)"
                return track

        msg = "No track selected."
        raise ValueError(msg)

    def _get_fallback_selection(self, tracks: list[dict[str, Any]]) -> str:
        """Generate a fallback menu for selecting a track."""
        choices = sorted([f"{track['track_name']}" for track in tracks]) + [
            "(skip adding metadata)"
        ]
        questions = [
            inquirer.List(
                "track",
                message=colored("Couldn't match filename. Select track", "yellow"),
                choices=choices,
                carousel=True,
            )
        ]
        answers = inquirer.prompt(questions)
        spinner.stop()
        if not answers:
            msg = "No track selected."
            raise TypeError(msg)

        self.logger.debug("Selected track: %s", answers["track"])
        return answers["track"]

    def _handle_skipped_metadata(self, audio_track: AudioTrack) -> dict:
        """Handle the case where the user skips adding metadata."""
        filename_question = [
            inquirer.Text(
                "confirmed_filename",
                message=colored("Confirm or edit the filename", "yellow"),
                default=audio_track.filename,
            )
        ]
        filename_answer = inquirer.prompt(filename_question)
        if not filename_answer:
            msg = "No filename confirmed."
            raise TypeError(msg)

        confirmed_filename = filename_answer["confirmed_filename"]

        self.logger.debug("Confirmed filename: %s", confirmed_filename)

        spinner.start()
        return {"file_name": confirmed_filename}
