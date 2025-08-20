from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import inquirer
from polykit.text import color as colored

from dsbin.wpmusic.audio_track import AudioTrack

if TYPE_CHECKING:
    from logging import Logger

    from halo import Halo

    from dsbin.wpmusic.configs import WPConfig
    from dsbin.wpmusic.metadata_handler import MetadataHandler


class TrackIdentifier:
    """Identify a track based on input file and metadata."""

    def __init__(self, config: WPConfig, metadata_handler: MetadataHandler, logger: Logger):
        self.config = config
        self.metadata_handler = metadata_handler
        self.logger = logger
        self.full_metadata = self.metadata_handler.full_metadata
        self.tracks = self.full_metadata.get("tracks", [])

        self.logger.debug("Loaded metadata with %s tracks.", len(self.tracks))

    def create_audio_track(
        self,
        file_path: Path,
        append_text: str = "",
        is_instrumental: bool | None = None,
        track_metadata: dict[str, Any] | None = None,
        spinner: Halo | None = None,
    ) -> AudioTrack:
        """Create a fully initialized AudioTrack object with metadata and cover art."""
        if track_metadata is None:  # If track_metadata is not provided, identify it first
            temp_track = AudioTrack(str(file_path), append_text=append_text)
            track_metadata = self.identify_track(temp_track, spinner)

        # Add metadata and cover art if metadata was not skipped, otherwise just basic metadata
        if metadata_skipped := len(track_metadata) == 1 and "track_name" in track_metadata:
            basic_metadata = self.full_metadata.get("metadata", {})
            final_metadata = {
                **track_metadata,
                "album_metadata": {"artist_name": basic_metadata.get("artist_name", "")},
            }
        else:
            final_metadata = {
                **track_metadata,
                "album_metadata": self.full_metadata.get("metadata", {}),
                "cover_data": self.metadata_handler.cover_data,
            }

        return AudioTrack(
            filename=str(file_path),
            append_text=append_text,
            track_metadata=final_metadata,
            instrumental=is_instrumental,
            metadata_skipped=metadata_skipped,
        )

    def identify_track(
        self, audio_track: AudioTrack, spinner: Halo | None = None
    ) -> dict[str, AudioTrack]:
        """Fetch track metadata based on the input file.

        Raises:
            TypeError: If no track is selected from the fallback menu.
        """
        if spinner:
            spinner.start(colored("Fetching track metadata...", "cyan"))

        try:
            return self._identify_by_name(audio_track)
        except ValueError:
            if spinner:
                spinner.stop()
            try:
                return self._identify_by_fallback_menu(audio_track)
            except TypeError as e:
                msg = "No track selected. Aborting."
                raise TypeError(msg) from e

    def _identify_by_name(self, audio_track: AudioTrack) -> dict[str, AudioTrack]:
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
        for track in self.tracks:
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
                self.logger.debug(
                    "Processing and uploading %s: %s", audio_track.filename, track["track_name"]
                )
                return track

        msg = "No track found in metadata."
        raise ValueError(msg)

    def _identify_by_fallback_menu(self, audio_track: AudioTrack) -> dict[str, AudioTrack]:
        """Given track data, display a menu to select a track and retrieve its metadata.

        Raises:
            ValueError: If no track is selected from the fallback menu.
        """
        self.logger.debug("No track found for filename '%s'.", audio_track.filename)

        selected_track_name = self._get_fallback_selection(self.tracks)

        if selected_track_name == "(skip adding metadata)":
            return self._handle_skipped_metadata(audio_track)

        for track in self.tracks:
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
        if not answers:
            msg = "No track selected."
            raise TypeError(msg)

        self.logger.debug("Selected track: %s", answers["track"])
        return answers["track"]

    def _handle_skipped_metadata(self, audio_track: AudioTrack) -> dict[str, Any]:
        """Handle the case where the user skips adding metadata.

        Raises:
            TypeError: If no filename is confirmed.
        """
        filename_question = [
            inquirer.Text(
                "confirmed_filename",
                message=colored("Confirm or edit the filename (without extension)", "yellow"),
                default=audio_track.filename,
            )
        ]
        filename_answer = inquirer.prompt(filename_question)
        if not filename_answer:
            msg = "No filename confirmed."
            raise TypeError(msg)

        confirmed_filename = filename_answer["confirmed_filename"]

        self.logger.debug("Confirmed filename: %s", confirmed_filename)
        return {"track_name": confirmed_filename}
