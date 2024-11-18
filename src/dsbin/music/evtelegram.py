#!/usr/bin/env python3

"""
Uploads my Evanescence remixes to a Telegram channel.

This script is designed to upload my Evanescence remixes to a Telegram channel. It can be used (with
slight modification) to upload any audio files to any Telegram channel.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
from io import BytesIO

import inquirer
import requests
from dotenv import load_dotenv
from mutagen.mp4 import MP4, MP4Cover
from PIL import Image
from pydub import AudioSegment

from dsutil.notifiers.send_telegram import TelegramSender
from dsutil.progress import halo_progress

TRACK_URL = "https://gitlab.dannystewart.com/danny/evremixes/-/raw/main/evtracks.json"

# Get the script directory and assemble paths
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIRECTORY, ".env")

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path=ENV_PATH)

# Initialize Telegram Bot API
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BOT_TOKEN = os.getenv("EV_TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("EV_TELEGRAM_CHANNEL_ID")

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Upload audio tracks to Telegram channel.")
    parser.add_argument("--comment", action="store_true", help="Include comments on uploads")
    return parser.parse_args()


def prepare_track_details() -> requests.Response:
    """Download and return the JSON file with track details."""
    return requests.get(TRACK_URL, timeout=5)


def get_track_details() -> tuple[dict, dict, bytes]:
    """Download track and album metadata, plus cover art."""
    with halo_progress(
        start_message="Downloading track details...", end_message="Downloaded track details."
    ):
        response = prepare_track_details()
        track_data = json.loads(response.text)
        metadata = track_data.get("metadata", {})
        cover_response = requests.get(metadata.get("cover_art_url", ""), timeout=5)
        cover_data_original = cover_response.content

        # Convert to JPEG and resize to 800x800 using PIL
        image = Image.open(BytesIO(cover_data_original))
        image = image.convert("RGB")  # Convert to RGB if image is not in this mode
        image = image.resize((800, 800))

        # Save the image data to a BytesIO object, then to a byte array
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        cover_data = buffered.getvalue()

    return track_data, metadata, cover_data


def get_selected_tracks(track_data: dict) -> list[dict]:
    """
    Sort tracks and display menu for track selection.

    Args:
        track_data: The track data.

    Returns:
        The selected tracks sorted by start date.
    """
    sorted_tracks = sorted(track_data["tracks"], key=lambda x: x["start_date"], reverse=True)
    questions = [
        inquirer.Checkbox(
            "tracks",
            message="Select tracks to upload (Ctrl-A for all)",
            choices=[track["track_name"] for track in sorted_tracks],
        ),
    ]
    answers = inquirer.prompt(questions)
    if answers:
        selected_tracks = [
            track for track in sorted_tracks if track["track_name"] in answers["tracks"]
        ]

    return sorted(selected_tracks, key=lambda x: x["start_date"])


def collect_track_comments(selected_tracks: list[dict]) -> dict:
    """
    Collect any comments for the selected tracks.

    Args:
        selected_tracks: The selected tracks.

    Returns:
        The track comments.
    """
    track_comments = {}
    for track in selected_tracks:
        comment = input(f"Enter comment for {track['track_name']}: ")
        track_comments[track["track_name"]] = comment

    return track_comments


def upload_all_tracks(
    telegram_sender: TelegramSender,
    selected_tracks: list,
    metadata: dict,
    cover_data: bytes,
    track_comments: bool = None,
) -> None:
    """
    Upload all selected tracks to Telegram.

    Args:
        telegram_sender: The Telegram sender instance to use.
        selected_tracks: The selected tracks.
        metadata: The metadata for the album.
        cover_data: The cover art data.
        track_comments: The track comments. Defaults to None.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        output_folder = temp_dir

        for track in selected_tracks:
            upload_track(
                track, metadata, cover_data, output_folder, telegram_sender, track_comments
            )


def upload_track(
    track: dict,
    metadata: dict,
    cover_data: bytes,
    output_folder: str,
    telegram_sender: TelegramSender,
    track_comments: dict | None = None,
) -> None:
    """
    Upload a single track to Telegram.

    Args:
        track: The track data.
        metadata: The metadata for the album.
        cover_data: The cover art data.
        output_folder: The output folder for the audio files.
        telegram_sender: The Telegram sender instance to use.
        track_comments: The track comments. Defaults to None.
    """
    track_name = track["track_name"]
    file_url = track["file_url"]
    original_filename = os.path.basename(file_url)

    flac_file_path = _download_flac_file(track_name, original_filename, file_url, output_folder)

    # Rename file to just the song name
    renamed_flac_file_path = f"{output_folder}/{track_name}.flac"
    os.rename(flac_file_path, renamed_flac_file_path)

    m4a_file_path = _convert_flac_to_alac(track_name, renamed_flac_file_path, output_folder)
    duration = _add_metadata_and_get_duration(
        track, metadata, cover_data, m4a_file_path, track_name
    )

    with halo_progress(
        start_message=f"Uploading {track_name} to Telegram...",
        end_message=f"Uploaded {track_name} to Telegram.",
        fail_message=f"Failed to upload {track_name} to Telegram.",
    ) as spinner:
        try:
            telegram_sender.send_audio_file(
                m4a_file_path,
                chat_id=CHANNEL_ID,
                caption=track_comments.get(track_name, None) if track_comments else None,
                duration=duration,
                title=track_name,
                performer=metadata.get("artist_name", ""),
            )
        except Exception:
            spinner.fail(f"Failed to upload {track_name}.")


def _download_flac_file(
    track_name: str, original_filename: str, file_url: str, output_folder: str
) -> str:
    """
    Download the FLAC file.

    Args:
        track_name: The track name.
        original_filename: The original filename.
        file_url: The file URL.
        output_folder: The output folder for the audio files.

    Returns:
        The path to the downloaded FLAC file.
    """
    with halo_progress(
        start_message=f"Downloading {track_name}...",
        end_message=f"Downloaded {track_name}.",
        fail_message="Failed",
    ):
        flac_file_path = f"{output_folder}/{original_filename}"
        response = requests.get(file_url, timeout=60)
        with open(flac_file_path, "wb") as f:
            f.write(response.content)

        return flac_file_path


def _convert_flac_to_alac(track_name: str, flac_file: str, output_folder: str) -> str:
    """
    Convert FLAC to ALAC (Apple Lossless) M4A file.

    Args:
        track_name: The track name.
        flac_file: The path to the renamed FLAC file.
        output_folder: The output folder for the audio files.

    Returns:
        str: The path to the converted M4A file.
    """
    with halo_progress(
        start_message=f"Converting {track_name} to ALAC...",
        end_message=f"Converted {track_name} to ALAC.",
        fail_message=f"Failed to convert {track_name} to ALAC.",
    ):
        m4a_file_path = f"{output_folder}/{track_name}.m4a"
        audio = AudioSegment.from_file(flac_file, format="flac")
        audio.export(m4a_file_path, format="ipod", codec="alac")

        return m4a_file_path


def _add_metadata_and_get_duration(
    track: dict, metadata: dict, cover_data: bytes, m4a_file: str, track_name: str
) -> int:
    """
    Add metadata and cover art using Mutagen.

    Args:
        track: The track data.
        metadata: The metadata for the album.
        cover_data: The cover art data.
        m4a_file: The path to the M4A file.
        track_name: The track name.

    Returns:
        int: The duration of the audio in seconds.
    """
    with halo_progress(
        start_message=f"Adding metadata and cover art to {track_name}...",
        end_message=f"Added metadata and cover art to {track_name}.",
    ):
        audio = MP4(m4a_file)
        audio["trkn"] = [(track.get("track_number", 0), 0)]
        audio["\xa9nam"] = track.get("track_name", "")
        audio["\xa9ART"] = metadata.get("artist_name", "")
        audio["\xa9alb"] = metadata.get("album_name", "")
        audio["\xa9day"] = str(metadata.get("year", ""))
        audio["\xa9gen"] = metadata.get("genre", "")
        audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
        duration = int(audio.info.length)

        if "album_artist" in metadata:
            audio["aART"] = metadata.get("album_artist", "")
        if "comments" in track:
            audio["\xa9cmt"] = track["comments"]

        audio.save()
        return duration


def main() -> None:
    """Main function."""
    track_comments = {}
    if BOT_TOKEN is None or CHANNEL_ID is None:
        print("Error: Telegram info not found. Check environment variables.")
        sys.exit(1)

    args = parse_args()

    # Include comments if argument is supplied
    track_data, metadata, cover_data = get_track_details()

    # Sort selected tracks by start_date for the upload process
    selected_tracks = get_selected_tracks(track_data)

    if bool(args.comment):
        track_comments = collect_track_comments(selected_tracks)

    telegram_sender = TelegramSender(BOT_TOKEN, CHAT_ID)
    upload_all_tracks(telegram_sender, selected_tracks, metadata, cover_data, track_comments)


if __name__ == "__main__":
    main()
