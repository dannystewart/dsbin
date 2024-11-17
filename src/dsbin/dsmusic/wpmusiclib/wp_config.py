from __future__ import annotations

import os
from dataclasses import dataclass, field

import paramiko
from dotenv import load_dotenv
from halo import Halo

spinner = Halo(text="Initializing", spinner="dots")

# Local paths
LOCAL_SAVE_PATH: str = os.path.expanduser("~/Downloads")
LOCAL_DB_PATH: str = os.path.expanduser("~/Logic/Evanescence/.upload_log.db")
SSH_HOST: str = "dannystewart.com"
SSH_USER: str = "danny"
SSH_PRIVATE_KEY_PATH: str = os.path.expanduser("~/.ssh/id_rsa")

# Server paths and URLs
UPLOAD_PATH_PREFIX: str = "/mnt/docker/web/www/wordpress/wp-content/uploads/sites/2/"
UPLOAD_URL_PREFIX: str = "https://music.dannystewart.com/wp-content/uploads/sites/2/"

# Database settings
DB_HOST: str = "127.0.0.1"
DB_NAME: str = "music_uploads"
DB_USER: str = "music_uploads"
DB_PORT: int = 3306

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

    # Whether to skip the local database cache
    no_cache: bool = False

    # Paths and URLs
    save_path: str = field(default=LOCAL_SAVE_PATH)
    local_sqlite_db: str = field(default=LOCAL_DB_PATH)
    upload_path_prefix: str = field(default=UPLOAD_PATH_PREFIX)
    upload_url_prefix: str = field(default=UPLOAD_URL_PREFIX)

    # SSH settings
    private_key_path: str = field(default=SSH_PRIVATE_KEY_PATH)
    ssh_host: str = field(default=SSH_HOST)
    ssh_user: str = field(default=SSH_USER)
    _private_key: paramiko.RSAKey | None = field(default=None, init=False)
    ssh_passphrase: str = field(init=False)

    # Database settings
    db_host: str = field(default=DB_HOST)
    db_name: str = field(default=DB_NAME)
    db_port: int = field(default=DB_PORT)
    db_user: str = field(default=DB_USER)
    db_password: str = field(init=False)

    # Supported file formats
    formats: dict[str, str] = field(default_factory=lambda: SUPPORTED_FORMATS.copy())

    # Formats for conversion and upload
    formats_to_convert: list[str] = field(default_factory=lambda: ENABLED_FORMATS.copy())
    formats_to_upload: list[str] = field(default_factory=lambda: ENABLED_FORMATS.copy())

    def __post_init__(self):
        # Configure log level based on debug setting
        self.log_level = "debug" if self.debug else "info"

        # Load .env file
        dotenv_path = os.path.expanduser("~/.env")
        load_dotenv(dotenv_path)

        # Get SSH passphrase from environment
        self.ssh_passphrase = os.getenv("SSH_PASSPHRASE", "")

        # Get database credentials from environment
        self.db_password = os.getenv("MUSIC_UPLOADS_DB_PASSWORD", "")

        if not all([self.db_user, self.db_password]):
            msg = "Database credentials not found in environment."
            raise ValueError(msg)

    @property
    def private_key(self) -> paramiko.RSAKey:
        """Lazy load the SSH private key only when needed."""
        if self._private_key is None:
            self._private_key = paramiko.RSAKey.from_private_key_file(
                self.private_key_path, password=self.ssh_passphrase
            )
        return self._private_key
