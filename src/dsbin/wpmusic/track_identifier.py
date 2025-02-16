from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import inquirer

from dsutil import LocalLogger
from dsutil.text import color as colored

from dsbin.wpmusic.wp_config import Config, spinner

if TYPE_CHECKING:
    from dsbin.wpmusic.audio_track import AudioTrack


class TrackIdentifier:
    """Identify a track based on input file and metadata."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = LocalLogger().get_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            simple=self.config.log_simple,
        )

    def identify_track(self, audio_track: AudioTrack) -> dict:
        """Fetch track metadata based on the input file.

        Raises:
            TypeError: If no track is selected from the fallback menu.
        """
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
        """Identify the track by matching its upload filename against URLs in metadata.

        Raises:
            ValueError: If no track is found in the metadata.
        """
        self.logger.debug("Matching filename '%s' to track metadata...", audio_track.filename)

        # Remove "No Vocals" and strip the filename for comparison
        file_path = Path(audio_track.filename)
        formatted_file_name = str(file_path.stem).replace(" No Vocals", "").replace("'", "")
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
                    Path(track["file_url"].replace("'", "")).stem,
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
        """Given track data, display a menu to select a track and retrieve its metadata.

        Raises:
            ValueError: If no track is selected from the fallback menu.
        """
        self.logger.debug("No track found for filename '%s'.", audio_track.filename)

        selected_track_name = self._get_fallback_selection(audio_track.tracks)

        if selected_track_name == "(skip adding metadata)":
            return self._handle_skipped_metadata(audio_track)

        spinner.start()

        for track in audio_track.tracks:
            if track["track_name"] == selected_track_name:
                return track

        msg = "No track selected."
        raise ValueError(msg)

    def _get_fallback_selection(self, tracks: list[dict[str, Any]]) -> str:
        """Generate a fallback menu for selecting a track.

        Raises:
            TypeError: If no track is selected from the fallback menu.
        """
        choices = [
            *sorted([f"{track['track_name']}" for track in tracks]),
            "(skip adding metadata)",
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
        """Handle the case where the user skips adding metadata.

        Raises:
            TypeError: If no filename is confirmed.
        """
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
