#!/usr/bin/env python3

"""Uploads audio files to a Telegram channel.

To have this run automatically via Hazel, call it as an embedded script like this:
    source ~/.zshrc && $(pyenv which python) -m dsbin.music.pybounce "$1"
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import inquirer
from mutagen import File as MutagenFile  # type: ignore
from natsort import natsorted
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, DocumentAttributeAudio
from tqdm.asyncio import tqdm as async_tqdm

from dsbase import TZ, LocalLogger, configure_traceback
from dsbase.env import DSEnv
from dsbase.macos import get_timestamps
from dsbase.paths import DSPaths
from dsbase.shell import async_handle_keyboard_interrupt

from .pybounce_helpers import SQLiteManager

configure_traceback()

env = DSEnv()
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
logger = LocalLogger().get_logger(level=log_level)
logging.basicConfig(level=logging.WARNING)


class FileManager:
    """Manages selecting files and obtaining metadata."""

    def __init__(self):
        self.thread_pool = ThreadPoolExecutor()  # for running sync functions

    async def get_audio_files_in_current_dir(self) -> list[str]:
        """Get a list of audio files in the current directory and returns a sorted list."""

        def list_files() -> list[str]:
            extensions = ["wav", "aiff", "mp3", "m4a", "flac"]
            audio_files = [
                str(f)
                for ext in extensions
                for f in Path().iterdir()
                if f.suffix.lower() == f".{ext}" and f.is_file()
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
        """Get the Telegram channel entity for the given URL.

        Raises:
            ValueError: If the URL does not point to a channel or chat.
        """
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
        self, file_path: Path, comment: str, channel_entity: Channel | Chat
    ) -> None:
        """Upload the given file to the given channel.

        Args:
            file_path: The path to the file to upload.
            comment: A comment to include with the file.
            channel_entity: The channel entity to upload the file to.
        """
        file_path = Path(file_path)
        filename = file_path.name
        title = file_path.stem
        duration = await self.files.get_audio_duration(str(file_path))
        timestamp = await self.files.get_file_creation_time(str(file_path))

        # Format duration as M:SS
        minutes, seconds = divmod(duration, 60)
        formatted_duration = f"{minutes}m{seconds:02d}s"
        timestamp_text = f"{timestamp} • {formatted_duration}"

        logger.info("Uploading '%s' created %s.", filename, timestamp)
        logger.debug("Upload title: '%s'%s", title, f", with comment: {comment}" if comment else "")
        logger.debug("Uploading to %s (channel ID: %s)", env.channel_url, channel_entity.id)

        pbar = async_tqdm(
            total=file_path.stat().st_size,
            desc="Uploading",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
        )

        def update_progress(sent: int, _: int) -> None:
            pbar.update(sent - pbar.n)

        try:
            await self.client.send_file(
                channel_entity,
                str(file_path),
                caption=f"{title}\n{timestamp_text}\n{comment}",
                attributes=[DocumentAttributeAudio(duration=duration)],
                progress_callback=update_progress,
            )
        except (KeyboardInterrupt, asyncio.CancelledError):
            pbar.reset()
            pbar.close()
            logger.error("Upload cancelled by user.")
            return

        pbar.close()
        logger.info("'%s' uploaded successfully.", file_path)

    async def upload_files(
        self, files: list[Path], comment: str, channel_entity: Channel | Chat
    ) -> None:
        """Upload the given files to the channel."""
        for file in files:
            if Path(file).is_file():
                await self.post_file_to_channel(file, comment, channel_entity)
            else:
                logger.warning("'%s' is not a valid file. Skipping.", file)

    async def process_and_upload_file(
        self, file: Path, comment: str, channel_entity: Channel | Chat
    ) -> None:
        """Process a single file (convert if needed) and upload it to Telegram."""
        if not Path(file).is_file():
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
    sqlite = SQLiteManager(telegram.client)  # type: ignore

    try:
        await sqlite.start_client()
        channel_entity = await telegram.get_channel_entity()

        files_to_upload = []
        if args.files:
            for file_pattern in args.files:
                if file_pattern:
                    pattern_path = Path(file_pattern)
                    if pattern_path.is_absolute():
                        files_to_upload.append(pattern_path)
                    else:
                        files_to_upload.extend(Path().glob(file_pattern))

        # If no files were found or specified, fall back to interactive selection
        files_to_upload = list(dict.fromkeys(files_to_upload)) or await files.select_interactively()

        if files_to_upload:
            for file in files_to_upload:
                await telegram.process_and_upload_file(Path(file), args.comment, channel_entity)
        else:
            logger.warning("No files selected for upload.")

    finally:
        await sqlite.disconnect_client()
        files.thread_pool.shutdown()


def main() -> None:
    """Run the main function with asyncio."""
    try:
        asyncio.run(run())  # type: ignore
    except KeyboardInterrupt:
        logger.error("Upload canceled by user.")


if __name__ == "__main__":
    main()
