from __future__ import annotations

import os
import sqlite3
import subprocess
from contextlib import contextmanager
from typing import TYPE_CHECKING

import mysql.connector

from dsutil.log import LocalLogger

if TYPE_CHECKING:
    from collections.abc import Generator

    from mysql.connector.abstracts import MySQLConnectionAbstract
    from mysql.connector.pooling import PooledMySQLConnection

    from .wp_config import Config


class DatabaseManager:
    """Manages database connections with MySQL primary and SQLite cache."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = LocalLogger.setup_logger(self.__class__.__name__, level=self.config.log_level)

    def run(self, command: str) -> tuple[bool, str]:
        """Execute a shell command and return success status and output."""
        try:
            with subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            ) as process:
                output, _ = process.communicate()
                decoded_output = output.decode("utf-8").strip()
                return process.returncode == 0, decoded_output
        except subprocess.CalledProcessError as e:
            return False, e.output.decode("utf-8").strip()

    def ensure_ssh_tunnel(self, port: int, service_name: str = "SSH tunnel") -> None:
        """Check for an SSH tunnel on a specified port and establish one if needed."""
        self.logger.debug("Checking for existing %s on port %s...", service_name, port)
        self.kill_existing_ssh_tunnel(service_name, port)
        self.establish_ssh_tunnel(port, service_name)

    def kill_existing_ssh_tunnel(self, service_name: str, port: int) -> None:
        """Kill an existing SSH tunnel."""
        success, output = self.run(f"lsof -ti:{port} -sTCP:LISTEN")
        if success and output.strip():
            ssh_tunnel_pid = output.strip()
            self.logger.debug(
                "Found existing %s with PID: %s. Killing...", service_name, ssh_tunnel_pid
            )
            self.run(f"kill -9 {ssh_tunnel_pid}")
            self.logger.debug("Existing %s killed.", service_name)
        else:
            self.logger.debug("No existing %s found. Starting now...", service_name)

    def establish_ssh_tunnel(self, port: int, service_name: str) -> None:
        """Establish an SSH tunnel to a remote server."""
        success, _ = self.run(
            f"ssh -fNL {port}:localhost:{port} {self.config.ssh_user}@{self.config.ssh_host}"
        )
        if success:
            self.logger.debug("%s established.", service_name)
        else:
            msg = "Failed to establish SSH tunnel."
            raise DatabaseError(msg)

    @contextmanager
    def get_mysql_connection(
        self,
    ) -> Generator[MySQLConnectionAbstract | PooledMySQLConnection, None, None]:
        """Get MySQL connection through SSH tunnel."""
        self.ensure_ssh_tunnel(self.config.db_port, "MySQL SSH tunnel")

        try:
            conn = mysql.connector.connect(
                host=self.config.db_host,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                collation="utf8mb3_general_ci",
                charset="utf8mb3",
            )
            yield conn
        finally:
            if "conn" in locals():
                conn.close()
            self.kill_existing_ssh_tunnel("MySQL SSH tunnel", self.config.db_port)

    @contextmanager
    def get_read_connection(
        self, check_stale: bool = True
    ) -> Generator[
        sqlite3.Connection | MySQLConnectionAbstract | PooledMySQLConnection, None, None
    ]:
        """
        Get a connection for reading, using local cache if available and up-to-date.

        Args:
            check_stale: Whether to check if cache needs updating. Default True.
        """
        # If cache is disabled, wrap MySQL connection to match SQLite interface
        if self.config.no_cache:
            with self.get_mysql_connection() as conn:
                yield conn
            return

        try:
            if os.path.exists(self.config.upload_log_db):
                if check_stale and self.is_cache_stale():
                    self.logger.debug("Cache is stale, refreshing from MySQL.")
                    self.refresh_cache()
                else:
                    self.logger.debug("Using local SQLite cache for reading.")
                with sqlite3.connect(self.config.upload_log_db) as conn:
                    yield conn
            else:
                self.logger.debug("No local cache found, creating from MySQL.")
                self.refresh_cache()
                with sqlite3.connect(self.config.upload_log_db) as conn:
                    yield conn
        except Exception as e:
            msg = f"Failed to establish database connection: {str(e)}"
            raise DatabaseError(msg) from e

    def refresh_cache(self) -> None:
        """Refresh the local SQLite cache from MySQL."""
        with (
            self.get_mysql_connection() as mysql_conn,
            sqlite3.connect(self.config.upload_log_db) as sqlite_conn,
        ):
            # Create tables
            self._init_sqlite_schema(sqlite_conn)

            # Copy data from MySQL
            mysql_cursor = mysql_conn.cursor()
            sqlite_cursor = sqlite_conn.cursor()

            # Copy tracks
            mysql_cursor.execute("SELECT * FROM tracks")
            tracks = mysql_cursor.fetchall()
            sqlite_cursor.executemany(
                "INSERT OR REPLACE INTO tracks (id, name) VALUES (?, ?)", tracks
            )

            # Copy uploads
            mysql_cursor.execute("SELECT * FROM uploads")
            uploads = mysql_cursor.fetchall()
            sqlite_cursor.executemany(
                "INSERT OR REPLACE INTO uploads (id, track_id, filename, instrumental, uploaded) VALUES (?, ?, ?, ?, ?)",
                uploads,
            )

            sqlite_conn.commit()

    def force_refresh(self) -> None:
        """Force a refresh of the local cache from MySQL."""
        self.logger.debug("Forcing cache refresh from MySQL")
        if os.path.exists(self.config.upload_log_db):
            os.remove(self.config.upload_log_db)
        self.refresh_cache()

    def is_cache_stale(self) -> bool:
        """Check if local cache needs updating by comparing row counts."""
        if not os.path.exists(self.config.upload_log_db):
            self.logger.debug("No cache file exists.")
            return True

        try:
            with self.get_mysql_connection() as mysql_conn:
                mysql_cursor = mysql_conn.cursor()
                mysql_cursor.execute("SELECT COUNT(*) FROM uploads")
                result = mysql_cursor.fetchone()
                mysql_count = result[0] if result else 0

                with sqlite3.connect(self.config.upload_log_db) as sqlite_conn:
                    sqlite_cursor = sqlite_conn.cursor()
                    sqlite_cursor.execute("SELECT COUNT(*) FROM uploads")
                    result = sqlite_cursor.fetchone()
                    sqlite_count = result[0] if result else 0

                is_stale = mysql_count != sqlite_count
                self.logger.debug(
                    "Cache status check - MySQL: %s rows, SQLite: %s rows, Stale: %s",
                    mysql_count,
                    sqlite_count,
                    is_stale,
                )
                return is_stale

        except Exception as e:
            self.logger.warning("Failed to check cache staleness: %s", str(e))
            return True

    def _init_sqlite_schema(self, conn: sqlite3.Connection) -> None:
        """Initialize the SQLite schema."""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY,
                track_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                instrumental BOOLEAN NOT NULL,
                uploaded TIMESTAMP NOT NULL,
                FOREIGN KEY (track_id) REFERENCES tracks(id)
            )
        """)
        conn.commit()


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
