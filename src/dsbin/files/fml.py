#!/usr/bin/env python3

"""Uploads a file to Fastmail's file storage using WebDAV."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from requests import Session
from requests.auth import HTTPBasicAuth

from dsbase import configure_traceback
from dsbase.text import color as colored

configure_traceback()

# Load environment variables
script_directory = Path(__file__).resolve().parent
env_path = script_directory / ".env"
load_dotenv(dotenv_path=env_path)

# Set WebDAV URL and user agent
WEBDAV_URL = "https://myfiles.fastmail.com/Storage/"
USER_AGENT = "FastmailUploader/1.0"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Upload a file to Fastmail's file storage.")
    parser.add_argument("file_path", help="Path to the file to upload.")
    parser.add_argument(
        "-f",
        "--force",
        help="Force upload and overwrite the file if it exists",
        action="store_true",
    )
    return parser.parse_args()


def file_exists(
    session: Session, webdav_url: str, username: str, password: str, file_path: str
) -> bool:
    """Check if the file already exists in WebDAV."""
    file_name = Path(file_path).name
    response = session.head(
        webdav_url + file_name,
        auth=HTTPBasicAuth(username, password),
    )
    return response.status_code == 200


def upload_file(
    session: Session, webdav_url: str, username: str, password: str, file_path: str | Path
) -> bool:
    """Upload the file to WebDAV."""
    file_path = Path(file_path)
    with file_path.open("rb") as file:
        response = session.put(
            webdav_url + file_path.name,
            data=file,
            auth=HTTPBasicAuth(username, password),
        )
    return response.status_code in {200, 201, 204}


def main() -> None:
    """Main function."""
    args = parse_arguments()
    username = os.environ.get("FASTMAIL_USERNAME")
    password = os.environ.get("FASTMAIL_PASSWORD")

    if not username or not password:
        print(
            colored(
                "Error: The FASTMAIL_USERNAME and FASTMAIL_PASSWORD environment variables must be set.",
                "red",
            )
        )
        sys.exit(1)

    file_path = args.file_path
    force_upload = args.force

    try:
        with requests.Session() as session:
            session.headers.update({"User-Agent": USER_AGENT})

            if not force_upload and file_exists(session, WEBDAV_URL, username, password, file_path):
                print(colored(f"File already exists: {file_path}", "yellow"))
                return

            if upload_file(session, WEBDAV_URL, username, password, file_path):
                print(colored(f"Upload completed: {file_path}", "green"))
            else:
                print(colored(f"Upload failed: {file_path}", "red"))
    except requests.RequestException as e:
        print(colored(f"HTTP request error: {e}", "red"))
    except OSError as e:
        print(colored(f"Cannot open file: {e}", "red"))
    except Exception as e:
        print(colored(f"An unexpected error occurred: {e}", "red"))


if __name__ == "__main__":
    main()
