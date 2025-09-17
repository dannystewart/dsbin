"""Uploads and converts audio files to Azure Blob Storage.

This script is designed to upload and convert audio files to Azure Blob Storage, with
additional options for purging the Azure CDN cache and repopulating the CDN. It can also
be used to convert audio files locally without uploading to Azure.

The script can convert files to MP3, M4A, or FLAC, and can be used to convert individual
files as well as directories.

NOTE: This is largely deprecated now that I've switched to storing music directly on my
WordPress site due to increasingly unreliable Azure storage and/or CDN issues.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import ClassVar

import pyperclip
from azure.storage.blob import BlobServiceClient
from halo import Halo
from polykit import PolyArgs, PolyEnv, PolyLog
from pydub import AudioSegment
from termcolor import colored


class AzureUploader:
    """Class for uploading audio files to Azure Blob Storage."""

    CONTAINER_NAME: ClassVar[str] = "music"
    ALLOWED_FOLDERS: ClassVar[list[str]] = [
        "bm",
        "dw",
        "ev",
        "games",
        "kp",
        "marina",
        "misc",
        "old",
        "original",
        "random",
        "scores",
        "st",
    ]

    def __init__(self, upload_path: str, input_file: Path) -> None:
        self.logger = PolyLog.get_logger()

        # Split the upload path into subfolder and blob name
        self.upload_path: str = upload_path
        self.input_file: Path = input_file
        self.subfolder, self.blob_name = self.upload_path.split("/", 1)

        # Initialize environment variables and get the Azure connection string
        self.env: PolyEnv = PolyEnv()
        self.env.add_var(
            "AZURE_CONNECTION_STRING",
            attr_name="conn",
            description="Azure connection string",
            secret=True,
        )

        # Validate that the folder is one of the allowed folders
        self._validate_folder()

        # Initialize the blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(self.env.conn)
        self.container_client = self.blob_service_client.get_container_client("music")
        self.blob_client = self.container_client.get_blob_client(self.blob_name)

        # Get the relative path and input/output formats
        self.relative_path = f"/{self.subfolder}/{self.blob_name}"
        self.input_format = Path(self.input_file).suffix[1:]
        self.output_format = Path(self.blob_name).suffix[1:]

    def process_and_upload(self) -> None:
        """Process and upload to Azure."""
        conv_msg = f"Converting from {self.input_format.upper()} to {self.output_format.upper()}..."
        conversion_spinner = Halo(text=colored(conv_msg, "cyan"), spinner="dots").start()

        # Convert the audio file and get the temporary output file
        temp_output_file = self.convert_audio()

        conversion_spinner.succeed(colored("Conversion complete!", "green"))
        upload_spinner = Halo(text=colored("Uploading to Azure...", "cyan"), spinner="dots").start()

        # Upload the audio file to Azure
        try:
            self.upload_to_azure(temp_output_file)
            upload_spinner.succeed(colored("Upload complete!", "green"))
        except Exception as e:
            upload_spinner.fail(f"Failed to upload to Azure: {e}")
            return

        purge_msg = f"Purging CDN for {self.blob_name} (this may take a few minutes)..."
        purge_spinner = Halo(text=colored(purge_msg, "cyan"), spinner="dots").start()

        # Purge the Azure CDN cache
        try:
            self.purge_cdn_cache()
            purge_spinner.succeed(colored("CDN cache purged!", "green"))
        except Exception as e:
            purge_spinner.fail(f"Failed to purge CDN: {e}")

        populate_spinner = Halo(text=colored("Repopulating CDN...", "cyan"), spinner="dots").start()

        # Repopulate the Azure CDN
        try:
            self.repopulate_cdn()
            populate_spinner.succeed(colored("CDN repopulated!", "green"))
        except Exception as e:
            populate_spinner.fail(f"Failed to repopulate CDN: {e}")

        # Delete the temp file
        Path(temp_output_file).unlink()

        # Copy the final URL to the clipboard
        self._print_and_copy_url()

    def _print_and_copy_url(self) -> None:
        final_url = f"https://files.dannystewart.com/music/{self.upload_path}"
        self.logger.info("✔ All operations complete!")
        pyperclip.copy(final_url)
        self.logger.info("\nURL copied to clipboard: %s", final_url)

    def _validate_folder(self) -> None:
        if self.subfolder not in self.ALLOWED_FOLDERS:
            self.logger.error(
                "Folder must be one of the following: %s", ", ".join(self.ALLOWED_FOLDERS)
            )
            sys.exit(1)

    def convert_audio(self) -> str:
        """Convert an audio file to the specified format.

        Returns:
            Path to converted audio file.
        """
        audio = AudioSegment.from_file(self.input_file, format=self.input_format)
        with tempfile.NamedTemporaryFile(
            suffix=f".{self.output_format}", delete=False
        ) as temp_file:
            audio.export(temp_file.name, format=self.output_format)
            return temp_file.name

    def upload_to_azure(self, temp_output_file: str) -> None:
        """Upload a file to Azure Blob Storage.

        Raises:
            RuntimeError: If the upload fails.
        """
        blob_client = self.container_client.get_blob_client(self.blob_name)
        with Path(temp_output_file).open("rb") as data:
            try:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    content_settings={"cache_control": "no-cache, no-store, must-revalidate"},
                )
            except Exception as e:
                msg = f"Error occurred while uploading to Azure: {e}"
                raise RuntimeError(msg) from e

    def purge_cdn_cache(self) -> None:
        """Purges the Azure CDN cache for the specified blob.

        Raises:
            RuntimeError: If the purge fails.
        """
        try:
            subprocess.run(
                [
                    "az",
                    "cdn",
                    "endpoint",
                    "purge",
                    "--resource-group",
                    "dsfiles",
                    "--name",
                    "dsfiles",
                    "--profile-name",
                    "dsfiles",
                    "--content-paths",
                    self.relative_path,
                ],
                check=False,
                capture_output=True,
            )
        except Exception as e:
            msg = f"Failed to purge Azure CDN cache. Error: {e}"
            raise RuntimeError(msg) from e

    def repopulate_cdn(self) -> None:
        """Repopulates the Azure CDN for the specified blob.

        Raises:
            RuntimeError: If the repopulate fails.
        """
        try:
            blob_data = self.container_client.download_blob(self.blob_name)
        except Exception as e:
            msg = f"Failed to download blob {self.blob_name}. Error: {e!s}"
            raise RuntimeError(msg) from e

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = f"{temp_dir}/temp_{Path(self.blob_name).name}"
            with Path(temp_file_path).open("wb") as temp_file:
                temp_file.write(blob_data.readall())


def main() -> None:
    """Process and upload to Azure."""
    parser = PolyArgs(description="Upload and convert audio file to Azure Blob Storage")
    parser.add_argument(
        "upload_path",
        type=str,
        help="Azure Blob upload path. Format: <container>/<filename>",
    )
    parser.add_argument("input_file", type=str, help="Local input audio file")
    args = parser.parse_args()

    azure_connector = AzureUploader(args.upload_path, args.input_file)
    azure_connector.process_and_upload()
