from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AudioTrack:
    """Represent an audio file."""

    filename: str
    append_text: str = ""
    track_metadata: dict[str, Any] | None = None
    instrumental: bool | None = None

    # Automatically extracted attributes
    is_instrumental: bool = field(init=False)
    file_path: Path = field(init=False)
    file_extension: str = field(init=False)
    file_format: str = field(init=False)

    # Track attributes initialized from metadata
    track_number: int = field(init=False, default=0)
    track_name: str = field(init=False, default="")
    track_title: str = field(init=False, default="")
    artist_name: str = field(init=False, default="")
    album_name: str = field(init=False, default="")
    album_artist: str = field(init=False, default="")
    genre: str = field(init=False, default="")
    year: str = field(init=False, default="")
    file_url: str = field(init=False, default="")
    inst_url: str = field(init=False, default="")
    url: str = field(init=False, default="")
    cover_data: bytes | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Initialize the audio track and apply metadata if provided."""
        # Convert filename to Path and store it
        self.file_path = Path(self.filename)
        self.filename = str(self.file_path)

        # Get file attributes
        filename_str = str(self.file_path.name)
        self.is_instrumental = (
            "No Vocals" in filename_str if self.instrumental is None else self.instrumental
        )
        self.file_extension = self.file_path.suffix[1:].lower()
        self.file_format = "alac" if self.file_extension == "m4a" else self.file_extension

        # Apply metadata if provided
        if self.track_metadata:
            self._apply_metadata(self.track_metadata)

    def _apply_metadata(self, track_metadata: dict[str, Any]) -> None:
        """Apply metadata to the track attributes."""
        self.track_metadata = track_metadata

        # Extract track attributes
        self.track_number = track_metadata.get("track_number", 0)
        self.track_name = track_metadata.get("track_name", "")
        self.file_url = track_metadata.get("file_url", "")
        self.inst_url = track_metadata.get("inst_url", "")
        self.url = self.inst_url if self.is_instrumental else self.file_url

        # Extract album attributes
        album_metadata = track_metadata.get("album_metadata", {})
        self.album_name = album_metadata.get("album_name", "")
        self.album_artist = album_metadata.get("album_artist", "")
        self.artist_name = album_metadata.get("artist_name", "")
        self.genre = album_metadata.get("genre", "")
        self.year = album_metadata.get("year", "")

        # Set cover data
        self.cover_data = track_metadata.get("cover_data")

        # Prepare track title
        self.track_title = self.track_name
        if self.append_text:
            self.track_title += f" {self.append_text}"
        if self.is_instrumental:
            self.track_title += " (Instrumental)"
