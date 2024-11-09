from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from halo import Halo

spinner = Halo(text="Initializing", spinner="dots")

# Local paths
LOCAL_SAVE_PATH: str = os.path.expanduser("~/Downloads")
LOCAL_DB_PATH: str = os.path.expanduser("~/Logic/Evanescence/.upload_log.db")
SSH_PRIVATE_KEY_PATH: str = os.path.expanduser("~/.ssh/id_rsa")

# Server paths and URLs
UPLOAD_PATH_PREFIX: str = "/mnt/docker/web/www/wordpress/wp-content/uploads/sites/2/"
UPLOAD_URL_PREFIX: str = "https://music.dannystewart.com/wp-content/uploads/sites/2/"

# Default lists of supported and enabled file formats
SUPPORTED_FORMATS: dict[str, str] = {
    "flac": ".flac",
    "alac": ".m4a",
    "mp3": ".mp3",
}
ENABLED_FORMATS: list[str] = ["flac", "alac"]


@dataclass
class Config:
    """Establish configuration settings for the script."""

    skip_upload: bool
    keep_files: bool
    debug: bool
    log_level: str = field(init=False)

    # Paths and URLs
    save_path: str = field(default=LOCAL_SAVE_PATH)
    upload_log_db: str = field(default=LOCAL_DB_PATH)
    upload_path_prefix: str = field(default=UPLOAD_PATH_PREFIX)
    upload_url_prefix: str = field(default=UPLOAD_URL_PREFIX)

    # SSH settings
    private_key_path: str = field(default=SSH_PRIVATE_KEY_PATH)
    ssh_passphrase: str = field(init=False)

    # Supported file formats
    formats: dict[str, str] = field(default_factory=lambda: SUPPORTED_FORMATS.copy())

    # Formats for conversion and upload
    formats_to_convert: list[str] = field(default_factory=lambda: ENABLED_FORMATS.copy())
    formats_to_upload: list[str] = field(default_factory=lambda: ENABLED_FORMATS.copy())

    def __post_init__(self):
        # Configure log level based on debug setting
        self.log_level = "debug" if self.debug else "info"

        # Load .env file
        script_directory = os.path.dirname(os.path.abspath(__file__))
        dotenv_path = os.path.join(script_directory, ".env")
        load_dotenv(dotenv_path)

        # Get SSH passphrase from environment
        self.ssh_passphrase = os.getenv("SSH_PASSPHRASE", "")
