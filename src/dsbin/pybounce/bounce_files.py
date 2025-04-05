from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import inquirer
from mutagen import File as MutagenFile  # type: ignore
from natsort import natsorted
from polykit.files import PolyFile
from polykit.formatters import TZ

if TYPE_CHECKING:
    from logging import Logger


class BounceFileManager:
    """Manages selecting files and obtaining metadata."""

    def __init__(self, logger: Logger):
        self.logger: Logger = logger
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
            return int(audio.info.length) if audio.info.length else 0

        return await asyncio.get_event_loop().run_in_executor(self.thread_pool, read_duration)

    async def get_file_creation_time(self, file_path: str) -> str:
        """Get the formatted creation timestamp for the file."""

        def get_timestamp() -> str:
            ctime, _ = PolyFile.get_timestamps(Path(file_path))
            creation_date = datetime.strptime(ctime, "%m/%d/%Y %H:%M:%S").replace(tzinfo=TZ)
            return creation_date.strftime("%a %b %d at %-I:%M:%S %p").replace(" 0", " ")

        return await asyncio.get_event_loop().run_in_executor(self.thread_pool, get_timestamp)

    async def select_interactively(self) -> list[str]:
        """Prompt user to select files interactively."""
        audio_files = await self.get_audio_files_in_current_dir()
        if not audio_files:
            self.logger.warning("No audio files found in the current directory.")
            return []

        def prompt_user() -> list[str]:
            try:
                questions = [
                    inquirer.Checkbox(
                        "selected_files",
                        message="Select audio files to upload",
                        choices=audio_files,
                        carousel=True,
                    )
                ]
                answers = inquirer.prompt(questions)
                return answers["selected_files"] if answers else []
            except KeyboardInterrupt:
                self.logger.error("Upload canceled by user.")
                return []

        return await asyncio.get_event_loop().run_in_executor(self.thread_pool, prompt_user)
