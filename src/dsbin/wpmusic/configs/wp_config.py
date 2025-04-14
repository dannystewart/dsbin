from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import paramiko
from polykit.env import PolyEnv
from polykit.paths import PolyPath


@dataclass
class WPConfig:
    """Establish configuration settings for the script.

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
    log_level: str = field(init=False)
    log_simple: bool = True

    # Whether to skip the local database cache
    no_cache: bool = False

    # SSH settings
    ssh_passphrase: str = field(init=False)
    _private_key: paramiko.Ed25519Key | None = field(default=None, init=False)

    # Supported file formats
    formats: ClassVar[dict[str, str]] = {
        "flac": ".flac",
        "alac": ".m4a",
        "mp3": ".mp3",
    }
    formats_to_convert: ClassVar[list[str]] = ["flac", "alac"]
    formats_to_upload: ClassVar[list[str]] = ["flac", "alac"]

    def __post_init__(self):
        # Initialize environment variables
        self.env = PolyEnv()
        self.env.add_debug_var()
        self.env.add_var(
            "SSH_PASSPHRASE",
            description="SSH key passphrase",
            secret=True,
        )
        self.env.add_var(
            "WPMUSIC_METADATA_URL",
            attr_name="metadata_url",
            description="URL for fetching metadata",
        )
        self.env.add_var(
            "WPMUSIC_UPLOAD_PATH_PREFIX",
            attr_name="upload_path_prefix",
            description="Path prefix for music uploads",
        )
        self.env.add_var(
            "WPMUSIC_UPLOAD_URL_PREFIX",
            attr_name="upload_url_prefix",
            description="URL prefix for music uploads",
        )
        self.env.add_var(
            "WPMUSIC_UPLOADS_MYSQL_PASSWORD",
            attr_name="db_password",
            description="MySQL password for music_uploads user",
            secret=True,
        )

        # Initialize paths
        self.paths = PolyPath("wpmusic")
        self.file_save_path = self.paths.downloads_dir
        self.local_sqlite_db = self.paths.from_cache("wpmusic_uploads.db")

        # Database configuration
        self.db_host = "127.0.0.1"
        self.db_port = 3306
        self.db_name = "music_uploads"
        self.db_user = "music_uploads"
        self.db_password = self.env.db_password

        # Initialize SSH
        self.ssh_user = "danny"
        self.ssh_host = "dannystewart.com"
        self.ssh_passphrase = self.env.ssh_passphrase
        self.private_key_path = self.paths.get_ssh_key("id_ed25519")
        self._private_key: paramiko.Ed25519Key | None = None

        # Load environment variables into class attributes
        self.debug = self.env.debug
        self.metadata_url = self.env.metadata_url
        self.upload_path_prefix = self.env.upload_path_prefix
        self.upload_url_prefix = self.env.upload_url_prefix

        # Configure log level based on debug setting
        self.log_level = "debug" if self.env.debug else "info"

    @property
    def private_key(self) -> paramiko.Ed25519Key:
        """Lazy load the SSH private key only when needed."""
        if self._private_key is None:
            self._private_key = paramiko.Ed25519Key.from_private_key_file(
                self.private_key_path, password=self.ssh_passphrase
            )
        return self._private_key
