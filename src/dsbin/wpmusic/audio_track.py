from __future__ import annotations

import json
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image


@dataclass
class AudioTrack:
    """Represent an audio file."""

    filename: str
    metadata_url: str = "https://gitlab.dannystewart.com/danny/evremixes/raw/main/evtracks.json"
    append_text: str = ""

    # Automatically extracted attributes
    is_instrumental: bool = field(init=False)
    all_metadata: dict[str, Any] = field(init=False, default_factory=dict)
    album_metadata: dict[str, Any] = field(init=False, default_factory=dict)
    track_metadata: dict[str, Any] = field(init=False, default_factory=dict)
    cover_data: bytes | None = field(init=False, default=None)
    tracks: list[Any] = field(init=False, default_factory=list)
    file_path: Path = field(init=False)

    # Album attributes
    artist_name: str = field(init=False)
    album_name: str = field(init=False)
    album_artist: str = field(init=False)
    genre: str = field(init=False)
    year: str = field(init=False)

    # Track attributes
    track_number: int = field(init=False)
    track_name: str = field(init=False)
    track_title: str = field(init=False)
    file_extension: str = field(init=False)
    file_format: str = field(init=False)
    file_url: str = field(init=False, default="")
    inst_url: str = field(init=False, default="")
    url: str = field(init=False, default="")

    def __post_init__(self) -> None:
        """Initialize the audio track."""
        # Convert filename to Path and store it
        self.file_path = Path(self.filename)
        self.filename = str(self.file_path)

        # Get file attributes
        filename_str = str(self.file_path.name)
        self.is_instrumental = "No Vocals" in filename_str
        self.file_extension = self.file_path.suffix[1:].lower()
        self.file_format = "alac" if self.file_extension == "m4a" else self.file_extension

        # Fetch and set metadata
        self.all_metadata, self.cover_data = self.download_all_metadata()
        self.tracks = self.all_metadata.get("tracks", [])

    def set_track_metadata(self, track_metadata: dict[str, Any]) -> None:
        """Set the track metadata and extract relevant attributes."""
        self.track_metadata = track_metadata

        # Extract attributes from all_metadata, album_metadata, and track_metadata
        self.track_number = self.track_metadata.get("track_number", 0)
        self.album_metadata = self.all_metadata.get("metadata", {})
        self.album_name = self.album_metadata.get("album_name", "")
        self.album_artist = self.album_metadata.get("album_artist", "")
        self.artist_name = self.album_metadata.get("artist_name", "")
        self.genre = self.album_metadata.get("genre", "")
        self.year = self.album_metadata.get("year", "")
        self.track_name = self.track_metadata.get("track_name", "")
        self.file_url = self.track_metadata.get("file_url", "")
        self.inst_url = self.track_metadata.get("inst_url", "")
        self.url = self.inst_url if self.is_instrumental else self.file_url

        # Prepare track title with optional append text and instrumental label
        self.track_title = self.track_name
        if self.append_text:
            self.track_title += f" {self.append_text}"
        if self.is_instrumental:
            self.track_title += " (Instrumental)"

    def download_all_metadata(self) -> tuple[dict[str, Any], bytes | None]:
        """Retrieve and prepare metadata for the album and all tracks, and download cover art."""
        response = requests.get(self.metadata_url, timeout=10)
        all_metadata = json.loads(response.text)
        cover_data = None

        if cover_art_url := all_metadata.get("metadata", {}).get("cover_art_url", ""):
            cover_data = self.download_cover_art(cover_art_url)

        return all_metadata, cover_data

    @staticmethod
    def download_cover_art(url: str) -> bytes | None:
        """Download cover art from the given URL and return the bytes."""
        response = requests.get(url, timeout=10)
        cover_art_bytes = BytesIO(response.content)
        cover_image = Image.open(cover_art_bytes).convert("RGB")
        cover_data = cover_image.resize((800, 800))
        buffered = BytesIO()
        cover_data.save(buffered, format="JPEG")

        return buffered.getvalue()
