"""
Uploads and converts audio files to Azure Blob Storage.

This script is designed to upload and convert audio files to Azure Blob Storage, with
additional options for purging the Azure CDN cache and repopulating the CDN. It can also
be used to convert audio files locally without uploading to Azure.

The script can convert files to MP3, M4A, or FLAC, and can be used to convert individual
files as well as directories.

NOTE: This is largely deprecated now that I've switched to storing music directly on my
WordPress site due to increasingly unreliable Azure storage and/or CDN issues.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import warnings
from typing import Any

import pyperclip
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from halo import Halo
from pydub import AudioSegment
from termcolor import colored

from dsutil import configure_traceback

configure_traceback()
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Initialize spinner, temp dir, env vars, and Azure client
spinner = Halo(text="Initializing", spinner="dots")
temp_dir = tempfile.mkdtemp()
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
connection_string = os.getenv("AZURE_CONNECTION_STRING", "")


# Variables
CONTAINER_NAME = "music"
ALLOWED_FOLDERS = [
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


def validate_folder(folder: str) -> None:
    """
    Validate that the folder is one of the allowed folders.

    Args:
        folder: Folder name.
    """
    if folder not in ALLOWED_FOLDERS:
        msg = f"Folder must be one of the following: {', '.join(ALLOWED_FOLDERS)}"
        raise ValueError(msg)


def convert_audio(input_file: str, output_format: str) -> str:
    """
    Convert an audio file to the specified format.

    Args:
        input_file: Input audio file.
        output_format: Output audio format.

    Returns:
        Path to converted audio file.
    """
    input_format = os.path.splitext(input_file)[1][1:]
    audio = AudioSegment.from_file(input_file, format=input_format)
    with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as temp_file:
        audio.export(temp_file.name, format=output_format)
        return temp_file.name


def upload_to_azure(client: Any, blob_name: str, temp_output_file: str) -> None:
    """
    Upload a file to Azure Blob Storage.

    Args:
        client: Azure Blob client.
        blob_name: Azure Blob name.
        temp_output_file: Path to temporary output file.

    Raises:
        Exception: If the upload fails.
    """
    blob_client = client.get_blob_client(blob_name)
    with open(temp_output_file, "rb") as data:
        try:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings={"cache_control": "no-cache, no-store, must-revalidate"},
            )
        except Exception as e:
            msg = f"Error occurred while uploading to Azure: {e}"
            raise Exception(msg) from e


def purge_cdn_cache(subfolder: str, blob_name: str) -> None:
    """
    Purges the Azure CDN cache for the specified blob.

    Args:
        subfolder: Blob subfolder.
        blob_name: Blob name.

    Raises:
        Exception: If the purge fails.
    """
    relative_path = f"/{subfolder}/{blob_name}"
    process = subprocess.run(
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
            relative_path,
        ],
        capture_output=True,
    )

    if process.returncode != 0:
        msg = f"Failed to purge Azure CDN cache. Error: {process.stderr.decode('utf-8')}"
        raise Exception(msg)


def repopulate_cdn(client: Any, blob_name: str) -> None:
    """
    Repopulates the Azure CDN for the specified blob.

    Args:
        client: Azure Blob client.
        blob_name: Blob name.

    Raises:
        Exception: If the repopulate fails.
    """
    try:
        blob_data = client.download_blob()
    except Exception as e:
        msg = f"Failed to download blob {blob_name}. Error: {str(e)}"
        raise Exception(msg) from e

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_file_path = f"{tmp_dir}/temp_{os.path.basename(blob_name)}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(blob_data.readall())


def process_and_upload(upload_path: str, input_file: str) -> None:
    """Process and upload to Azure."""
    connect_str = os.getenv("AZURE_CONNECTION_STRING")
    if not connect_str:
        print(
            colored(
                "Error: AZURE_CONNECTION_STRING not found. Check environment variables.",
                "red",
            )
        )
        sys.exit(1)

    client = BlobServiceClient.from_connection_string(connect_str).get_container_client("music")

    subfolder, blob_name = upload_path.split("/", 1)
    validate_folder(subfolder)

    # Determine input and output formats
    input_format = os.path.splitext(input_file)[1][1:]
    output_format = os.path.splitext(blob_name)[1][1:]
    conversion_spinner = Halo(
        text=colored(
            f"Converting from {input_format.upper()} to {output_format.upper()}...",
            "cyan",
        ),
        spinner="dots",
    ).start()
    temp_output_file = convert_audio(input_file, output_format)
    conversion_spinner.succeed(colored("Conversion complete!", "green"))

    upload_spinner = Halo(text=colored("Uploading to Azure...", "cyan"), spinner="dots").start()
    try:
        upload_to_azure(client, f"{subfolder}/{blob_name}", temp_output_file)
        upload_spinner.succeed(colored("Upload complete!", "green"))
    except Exception as e:
        upload_spinner.fail(f"Failed to upload to Azure: {e}")
        return

    purge_spinner = Halo(
        text=colored(
            f"Purging CDN for {blob_name} (this may take a few minutes)...",
            "cyan",
        ),
        spinner="dots",
    ).start()
    try:
        purge_cdn_cache(subfolder, blob_name)
        purge_spinner.succeed(colored("CDN cache purged!", "green"))
    except Exception as e:
        purge_spinner.fail(f"Failed to purge CDN: {e}")

    repopulate_spinner = Halo(
        text=colored("Repopulating CDN...", "cyan"),
        spinner="dots",
    ).start()
    try:
        repopulate_cdn(client, blob_name)
        repopulate_spinner.succeed(colored("CDN repopulated!", "green"))
    except Exception as e:
        repopulate_spinner.fail(f"Failed to repopulate CDN: {e}")

    os.remove(temp_output_file)

    final_url = f"https://files.dannystewart.com/music/{upload_path}"
    print(colored("✔ All operations complete!", "green"))
    pyperclip.copy(final_url)
    print("\nURL copied to clipboard:")
    print(colored(f"{final_url}", "blue"))


def main() -> None:
    """Process and upload to Azure."""
    parser = argparse.ArgumentParser(
        description="Upload and convert audio file to Azure Blob Storage."
    )
    parser.add_argument(
        "upload_path",
        type=str,
        help="Azure Blob upload path. Format: <container>/<filename>",
    )
    parser.add_argument("input_file", type=str, help="Local input audio file")

    args = parser.parse_args()
    process_and_upload(args.upload_path, args.input_file)
