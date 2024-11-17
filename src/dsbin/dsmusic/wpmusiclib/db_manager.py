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

    def _ensure_mysql_tunnel(self) -> None:
        """Ensure MySQL SSH tunnel exists and is working."""
        # Check for existing tunnel
        success, output = subprocess.getstatusoutput("lsof -ti:3306 -sTCP:LISTEN")
        if success == 0 and output.strip():
            self.logger.debug("Found existing MySQL tunnel (PID: %s). Killing...", output.strip())
            subprocess.run(["kill", "-9", output.strip()], check=False)
            self.logger.debug("Existing tunnel killed.")

        # Create new tunnel
        self.logger.debug("Starting MySQL tunnel...")
        cmd = f"ssh -fNL 3306:localhost:3306 {self.config.ssh_user}@{self.config.ssh_host}"
        if subprocess.run(cmd, shell=True, check=False).returncode != 0:
            msg = "Failed to establish MySQL tunnel"
            raise DatabaseError(msg)

        self.logger.debug("MySQL tunnel established.")

    @contextmanager
    def get_mysql_connection(
        self,
    ) -> Generator[MySQLConnectionAbstract | PooledMySQLConnection, None, None]:
        """Get MySQL connection through SSH tunnel."""
        self._ensure_mysql_tunnel()

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
