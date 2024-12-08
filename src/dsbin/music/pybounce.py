#!/usr/bin/env python3

"""
Uploads audio files to a Telegram channel.

To have this run automatically via Hazel, call it as an embedded script like this:
    ❯ source ~/.zshrc && $(pyenv which python) -m dsbin.music.pybounce "$1"
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import logging
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Protocol

import inquirer
from mutagen import File as MutagenFile  # type: ignore
from natsort import natsorted
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, DocumentAttributeAudio
from tqdm.asyncio import tqdm as async_tqdm

from dsutil import TZ, LocalLogger, configure_traceback
from dsutil.animation import walking_animation
from dsutil.env import DSEnv
from dsutil.macos import get_timestamps
from dsutil.paths import DSPaths
from dsutil.shell import async_handle_keyboard_interrupt
from dsutil.tools import async_retry_on_exception

configure_traceback()

env = DSEnv("pybounce")
env.add_var("PYBOUNCE_TELEGRAM_API_ID", attr_name="api_id", var_type=str)
env.add_var("PYBOUNCE_TELEGRAM_API_HASH", attr_name="api_hash", var_type=str, secret=True)
env.add_var("PYBOUNCE_TELEGRAM_PHONE", attr_name="phone", var_type=str)
env.add_var("PYBOUNCE_TELEGRAM_CHANNEL_URL", attr_name="channel_url", var_type=str)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Upload audio files to a Telegram channel.")
    parser.add_argument("--debug", action="store_true", help="enable debug mode")
    parser.add_argument("files", nargs="*", help="files to upload")
    parser.add_argument("comment", nargs="?", default="", help="comment to add to the upload")
    return parser.parse_args()


# Parse command-line arguments
args_for_logger = parse_arguments()

# Set up logger based on debug flag and set log level
log_level = "debug" if args_for_logger and args_for_logger.debug else "info"
logger = LocalLogger.setup_logger(level=log_level)
logging.basicConfig(level=logging.WARNING)


class TelegramClientProtocol(Protocol):
    """Protocol for the Telegram client."""

    async def start(self) -> None: ...  # noqa: D102

    async def disconnect(self) -> None: ...  # noqa: D102


class SQLiteManager:
    """Manages the SQLite database for the Telegram client."""

    # Retry configuration
    RETRY_TRIES = 5
    RETRY_DELAY = 5

    def __init__(self, client: TelegramClientProtocol) -> None:
        self.client = client

    @async_retry_on_exception(
        sqlite3.OperationalError, tries=RETRY_TRIES, delay=RETRY_DELAY, logger=logging
    )
    async def start_client(self) -> None:
        """Start the client safely, retrying if a sqlite3.OperationalError occurs."""
        with walking_animation():
            await self.client.start()

    @async_retry_on_exception(
        sqlite3.OperationalError, tries=RETRY_TRIES, delay=RETRY_DELAY, logger=logging
    )
    async def disconnect_client(self) -> None:
        """Disconnects the client safely, retrying if a sqlite3.OperationalError occurs."""
        await self.client.disconnect()


class FileManager:
    """Manages selecting files and obtaining metadata."""

    def __init__(self):
        self.thread_pool = ThreadPoolExecutor()  # for running sync functions

    async def get_audio_files_in_current_dir(self) -> list[str]:
        """Get a list of audio files in the current directory and returns a sorted list."""

        def list_files() -> list[str]:
            extensions = ["wav", "aiff", "mp3", "m4a", "flac"]
            audio_files = [
                f
                for ext in extensions
                for f in os.listdir(".")
                if f.lower().endswith(f".{ext}") and os.path.isfile(f)
            ]
            return natsorted(audio_files)

        return await asyncio.get_event_loop().run_in_executor(self.thread_pool, list_files)

    async def get_audio_duration(self, file_path: str) -> int:
        """Get the duration of the audio file in seconds."""

        def read_duration() -> int:
            audio = MutagenFile(file_path)
            return int(audio.info.length)

        return await asyncio.get_event_loop().run_in_executor(self.thread_pool, read_duration)

    async def get_file_creation_time(self, file_path: str) -> str:
        """Get the formatted creation timestamp for the file."""

        def get_timestamp() -> str:
            ctime, _ = get_timestamps(file_path)
            creation_date = datetime.strptime(ctime, "%m/%d/%Y %H:%M:%S").replace(tzinfo=TZ)
            return creation_date.strftime("%a %b %d at %-I:%M:%S %p").replace(" 0", " ")

        return await asyncio.get_event_loop().run_in_executor(self.thread_pool, get_timestamp)

    async def select_interactively(self) -> list[str]:
        """Prompt user to select files interactively."""
        audio_files = await self.get_audio_files_in_current_dir()
        if not audio_files:
            logger.warning("No audio files found in the current directory.")
            return []

        def prompt_user() -> list[str]:
            try:
                questions = [
                    inquirer.Checkbox(
                        "selected_files",
                        message="Select audio files to upload:",
                        choices=audio_files,
                        carousel=True,
                    )
                ]
                answers = inquirer.prompt(questions)
                return answers["selected_files"] if answers else []
            except KeyboardInterrupt:
                logger.error("Upload canceled by user.")
                return []

        return await asyncio.get_event_loop().run_in_executor(self.thread_pool, prompt_user)


class TelegramUploader:
    """Manages the Telegram client and uploads files to a channel."""

    def __init__(self, files: FileManager) -> None:
        self.files = files

        if not isinstance(env.channel_url, str):
            msg = "No channel URL provided in the .env file."
            raise RuntimeError(msg)

        # Set up session file and client
        self.paths = DSPaths("pybounce")
        self.session_file = self.paths.get_config_path(f"{env.phone}.session")
        self.client = TelegramClient(str(self.session_file), env.api_id, env.api_hash)

    async def get_channel_entity(self) -> Channel | Chat:
        """Get the Telegram channel entity for the given URL."""
        try:
            entity = await self.client.get_entity(env.channel_url)
            if not isinstance(entity, Channel | Chat):
                msg = "URL does not point to a channel or chat."
                raise ValueError(msg)
            return entity
        except ValueError:
            logger.error("Could not find the channel for the URL: %s", env.channel_url)
            raise

    async def post_file_to_channel(
        self, file_path: str, comment: str, channel_entity: Channel | Chat
    ) -> None:
        """
        Upload the given file to the given channel.

        Args:
            file_path: The path to the file to upload.
            comment: A comment to include with the file.
            channel_entity: The channel entity to upload the file to.
        """
        filename = os.path.basename(file_path)
        title = os.path.splitext(filename)[0]
        duration = await self.files.get_audio_duration(file_path)
        timestamp = await self.files.get_file_creation_time(file_path)

        # Format duration as M:SS
        minutes, seconds = divmod(duration, 60)
        formatted_duration = f"{minutes}m{seconds:02d}s"
        timestamp_text = f"{timestamp} • {formatted_duration}"

        logger.info("Uploading '%s' created %s.", filename, timestamp)
        logger.debug("Upload title: '%s'%s", title, f", with comment: {comment}" if comment else "")
        logger.debug("Uploading to %s (channel ID: %s)", env.channel_url, channel_entity.id)

        pbar = async_tqdm(
            total=os.path.getsize(file_path),
            desc="Uploading",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
        )

        try:
            await self.client.send_file(
                channel_entity,
                file_path,
                caption=f"{title}\n{timestamp_text}\n{comment}",
                attributes=[DocumentAttributeAudio(duration=duration)],
                progress_callback=lambda sent, _: pbar.update(sent - pbar.n),
            )
        except (KeyboardInterrupt, asyncio.CancelledError):
            pbar.reset()
            pbar.close()
            logger.error("Upload cancelled by user.")
            return

        pbar.close()
        logger.info("'%s' uploaded successfully.", file_path)

    async def upload_files(
        self, files: list[str], comment: str, channel_entity: Channel | Chat
    ) -> None:
        """Upload the given files to the channel."""
        for file in files:
            if os.path.isfile(file):
                await self.post_file_to_channel(file, comment, channel_entity)
            else:
                logger.warning("'%s' is not a valid file. Skipping.", file)

    async def process_and_upload_file(
        self, file: str, comment: str, channel_entity: Channel | Chat
    ) -> None:
        """Process a single file (convert if needed) and upload it to Telegram."""
        if not os.path.isfile(file):
            logger.warning("'%s' is not a valid file. Skipping.", file)
            return
        try:
            await self.post_file_to_channel(file, comment, channel_entity)

        except Exception as e:
            logger.error("Error processing '%s': %s", file, str(e))
            logger.warning("Skipping '%s'.", file)


@async_handle_keyboard_interrupt()
async def run() -> None:
    """Upload files to a Telegram channel."""
    # Parse command-line arguments
    args = parse_arguments()

    files = FileManager()
    telegram = TelegramUploader(files)
    sqlite = SQLiteManager(telegram.client)

    try:
        await sqlite.start_client()
        channel_entity = await telegram.get_channel_entity()

        files_to_upload = []
        for file_pattern in args.files:
            files_to_upload.extend(glob.glob(file_pattern))

        # Remove duplicates while preserving order
        files_to_upload = list(dict.fromkeys(files_to_upload)) or await files.select_interactively()

        if files_to_upload:
            for file in files_to_upload:
                await telegram.process_and_upload_file(file, args.comment, channel_entity)
        else:
            logger.warning("No files selected for upload.")

    finally:
        await sqlite.disconnect_client()
        files.thread_pool.shutdown()


def main() -> None:
    """Run the main function with asyncio."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
