from __future__ import annotations

from typing import TYPE_CHECKING

from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC, TALB, TCON, TDRC, TIT2, TPE1, TRCK  # type: ignore
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover

# ruff: noqa: PLC2701
from polykit.log import Logician

if TYPE_CHECKING:
    from pathlib import Path

    from dsbin.wpmusic.audio_track import AudioTrack
    from dsbin.wpmusic.configs import WPConfig


class MetadataSetter:
    """Add metadata to audio files."""

    def __init__(self, config: WPConfig):
        self.config = config
        self.logger = Logician.get_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            simple=self.config.log_simple,
        )

    def apply_metadata(self, audio_track: AudioTrack, audio_format: str, path: Path) -> Path:
        """Prepare the metadata for the file based on its format.

        Raises:
            ValueError: If the file format is not supported.
        """
        self.logger.debug("Preparing %s file '%s'...", audio_format.upper(), path)

        audio: FLAC | MP4 | MP3

        if audio_format == "alac":
            audio = self.apply_alac_metadata(path, audio_track)

        elif audio_format == "flac":
            audio = self.apply_flac_metadata(path, audio_track)

        elif audio_format == "mp3":
            audio = self.apply_mp3_metadata(path, audio_track)

        else:
            msg = f"Unsupported file format: {audio_format}"
            raise ValueError(msg)

        audio.save()
        return path

    @staticmethod
    def apply_flac_metadata(file_path: Path, audio_track: AudioTrack) -> FLAC:
        """Set metadata for FLAC files."""
        audio = FLAC(file_path)
        audio["title"] = audio_track.track_title
        audio["tracknumber"] = str(audio_track.track_number)
        audio["album"] = audio_track.album_name
        audio["albumartist"] = audio_track.album_artist
        audio["artist"] = audio_track.artist_name
        audio["genre"] = audio_track.genre
        audio["date"] = str(audio_track.year)

        # Add cover art
        if audio_track.cover_data:
            img = Picture()
            img.data = audio_track.cover_data
            img.type = 3
            img.mime = "image/jpeg"
            img.desc = "Cover (front)"
            audio.add_picture(img)

        return audio

    @staticmethod
    def apply_alac_metadata(file_path: Path, audio_track: AudioTrack) -> MP4:
        """Set metadata for ALAC files."""
        audio = MP4(file_path)
        audio["\xa9nam"] = audio_track.track_title
        audio["trkn"] = [(audio_track.track_number, 0)]
        audio["\xa9ART"] = audio_track.artist_name
        audio["aART"] = audio_track.album_artist
        audio["\xa9alb"] = audio_track.album_name
        audio["\xa9gen"] = audio_track.genre
        audio["\xa9day"] = str(audio_track.year)

        # Add cover art
        if audio_track.cover_data:
            audio["covr"] = [MP4Cover(audio_track.cover_data, imageformat=MP4Cover.FORMAT_JPEG)]

        return audio

    @staticmethod
    def apply_mp3_metadata(file_path: Path, audio_track: AudioTrack) -> MP3:
        """Set metadata for MP3 files."""
        # Create a new ID3 object
        tags = ID3()

        # Add metadata
        tags.add(TIT2(encoding=3, text=audio_track.track_title))
        tags.add(TRCK(encoding=3, text=str(audio_track.track_number)))
        tags.add(TALB(encoding=3, text=audio_track.album_name))
        tags.add(TPE1(encoding=3, text=audio_track.artist_name))
        tags.add(TCON(encoding=3, text=audio_track.genre))
        tags.add(TDRC(encoding=3, text=str(audio_track.year)))

        # Add cover art
        if audio_track.cover_data:
            tags.add(
                APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="Cover (front)",
                    data=audio_track.cover_data,
                )
            )

        # Save the new tags directly to the file and reload the MP3
        tags.save(file_path)
        return MP3(file_path)
