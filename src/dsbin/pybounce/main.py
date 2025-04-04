"""Uploads audio files to a Telegram channel.

To have this run automatically via Hazel, call it as an embedded script like this:
    source ~/.zshrc && $(pyenv which python) -m pybounce.pybounce "$1"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from enviromancer import Enviromancer
from logician import Logician
from pathkeeper import PathKeeper
from polykit import polykit_setup
from polykit.shell import async_with_handle_interrupt
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, DocumentAttributeAudio
from tqdm.asyncio import tqdm as async_tqdm

from dsbin.pybounce.file_manager import FileManager
from dsbin.pybounce.sqlite_manager import SQLiteManager

if TYPE_CHECKING:
    from logging import Logger

polykit_setup()


class TelegramUploader:
    """Manages the Telegram client and uploads files to a channel."""

    def __init__(self, env: Enviromancer, files: FileManager, logger: Logger) -> None:
        self.env: Enviromancer = env
        self.files: FileManager = files
        self.logger: Logger = logger

        if not isinstance(env.channel_url, str):
            msg = "No channel URL provided in the .env file."
            raise RuntimeError(msg)

        # Get Telegram client info from the .env file
        self.channel_url: str = env.channel_url
        self.api_id: str = env.api_id
        self.api_hash: str = env.api_hash
        self.phone: str = env.phone

        # Set up session file and client
        self.paths = PathKeeper("pybounce")
        self.session_file = self.paths.from_config(f"{env.phone}.session")
        self.client = TelegramClient(str(self.session_file), env.api_id, env.api_hash)

    async def get_channel_entity(self) -> Channel | Chat:
        """Get the Telegram channel entity for the given URL.

        Raises:
            ValueError: If the URL does not point to a channel or chat.
        """
        try:
            entity = await self.client.get_entity(self.channel_url)
            if not isinstance(entity, Channel | Chat):
                msg = "URL does not point to a channel or chat."
                raise ValueError(msg)
            return entity
        except ValueError:
            self.logger.error("Could not find the channel for the URL: %s", self.channel_url)
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

        self.logger.info("Uploading '%s' created %s.", filename, timestamp)
        self.logger.debug(
            "Upload title: '%s'%s", title, f", with comment: {comment}" if comment else ""
        )
        self.logger.debug("Uploading to %s (channel ID: %s)", self.channel_url, channel_entity.id)

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
            self.logger.error("Upload canceled.")
            return

        pbar.close()
        self.logger.info("'%s' uploaded successfully.", file_path)

    async def upload_files(
        self, files: list[Path], comment: str, channel_entity: Channel | Chat
    ) -> None:
        """Upload the given files to the channel."""
        for file in files:
            if Path(file).is_file():
                await self.post_file_to_channel(file, comment, channel_entity)
            else:
                self.logger.warning("'%s' is not a valid file. Skipping.", file)

    async def process_and_upload_file(
        self, file: Path, comment: str, channel_entity: Channel | Chat
    ) -> None:
        """Process a single file (convert if needed) and upload it to Telegram."""
        if not Path(file).is_file():
            self.logger.warning("'%s' is not a valid file. Skipping.", file)
            return
        try:
            await self.post_file_to_channel(file, comment, channel_entity)

        except Exception as e:
            self.logger.error("Error processing '%s': %s", file, str(e))
            self.logger.warning("Skipping '%s'.", file)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Upload audio files to a Telegram channel.")
    parser.add_argument("files", nargs="*", help="files to upload")
    parser.add_argument("comment", nargs="?", default="", help="comment to add to the upload")

    # Return default args if being run by pdoc
    if len(sys.argv) > 0 and sys.argv[0].endswith("pdoc"):
        return argparse.Namespace(debug=False, files=[], comment="")
    return parser.parse_args()


async def pybounce(env: Enviromancer, logger: Logger) -> None:
    """Upload files to a Telegram channel."""
    args = parse_arguments()
    files = FileManager(logger)
    telegram = TelegramUploader(env, files, logger)
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
    env = Enviromancer()
    env.add_debug_var()
    env.add_var("PYBOUNCE_TELEGRAM_API_ID", attr_name="api_id", var_type=str)
    env.add_var("PYBOUNCE_TELEGRAM_API_HASH", attr_name="api_hash", var_type=str, secret=True)
    env.add_var("PYBOUNCE_TELEGRAM_PHONE", attr_name="phone", var_type=str)
    env.add_var("PYBOUNCE_TELEGRAM_CHANNEL_URL", attr_name="channel_url", var_type=str)

    logger = Logician.get_logger(level=env.log_level)

    async_with_handle_interrupt(pybounce, env, logger, message="Upload canceled.", logger=logger)


if __name__ == "__main__":
    main()
