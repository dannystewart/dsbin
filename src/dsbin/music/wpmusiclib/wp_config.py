from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import paramiko
from halo import Halo

from dsutil.env import DSEnv
from dsutil.paths import DSPaths

spinner = Halo(text="Initializing", spinner="dots")


@dataclass
class Config:
    """
    Establish configuration settings for the script.

    Uses DSPaths for path management and DSEnv for environment variables. Initializes all required
    paths, environment variables, and subsystem configurations (SSH, database, etc.).

    Paths are managed through self.paths (DSPaths instance):
        self.file_save_path = self.paths.get_downloads_path()
        self.local_sqlite_db = self.paths.get_cache_path("wpmusic_uploads.db")

    Environment variables are managed through self.env (DSEnv instance):
        self.ssh_passphrase = self.env.ssh_passphrase
        self.db_password    = self.env.db_password
    """

    skip_upload: bool
    keep_files: bool
    debug: bool
    log_level: str = field(init=False)
    log_message_only: bool = False

    # Whether to skip the local database cache
    no_cache: bool = False

    # Paths and URLs
    upload_path_prefix: ClassVar[str] = "/mnt/docker/web/www/wordpress/wp-content/uploads/sites/2/"
    upload_url_prefix: ClassVar[str] = "https://music.dannystewart.com/wp-content/uploads/sites/2/"

    # SSH settings
    ssh_passphrase: str = field(init=False)
    _private_key: paramiko.RSAKey | None = field(default=None, init=False)

    # Supported file formats
    formats: ClassVar[dict[str, str]] = {
        "flac": ".flac",
        "alac": ".m4a",
        "mp3": ".mp3",
    }
    formats_to_convert: ClassVar[list[str]] = ["flac", "alac"]
    formats_to_upload: ClassVar[list[str]] = ["flac", "alac"]

    def __post_init__(self):
        # Configure log level based on debug setting
        self.log_level = "debug" if self.debug else "info"

        # Initialize core services
        self.paths = DSPaths("wpmusic")
        self.initialize_env_vars()

        # Set up paths
        self.file_save_path = self.paths.downloads_dir
        self.local_sqlite_db = self.paths.get_cache_path("wpmusic_uploads.db")

        # Initialize subsystems
        self.initialize_ssh()
        self.initialize_database()

    def initialize_env_vars(self) -> None:
        """Get environment variables."""
        self.env = DSEnv("wpmusic")

        # Set up required environment variables
        self.env.add_var(
            "SSH_PASSPHRASE",
            description="SSH key passphrase",
            secret=True,
        )
        self.env.add_var(
            "DSMUSIC_UPLOADS_MYSQL_PASSWORD",
            attr_name="db_password",
            description="MySQL password for music_uploads user",
            secret=True,
        )

    def initialize_ssh(self) -> None:
        """Initialize SSH settings."""
        self.ssh_host = "dannystewart.com"
        self.ssh_user = "danny"
        self.ssh_passphrase = self.env.ssh_passphrase
        self.private_key_path = self.paths.get_ssh_key("id_rsa")
        self._private_key: paramiko.RSAKey | None = None

    def initialize_database(self) -> None:
        """Initialize database settings."""
        self.db_host = "127.0.0.1"
        self.db_port = 3306
        self.db_name = "music_uploads"
        self.db_user = "music_uploads"
        self.db_password = self.env.db_password

    @property
    def private_key(self) -> paramiko.RSAKey:
        """Lazy load the SSH private key only when needed."""
        if self._private_key is None:
            self._private_key = paramiko.RSAKey.from_private_key_file(
                self.private_key_path, password=self.ssh_passphrase
            )
        return self._private_key
