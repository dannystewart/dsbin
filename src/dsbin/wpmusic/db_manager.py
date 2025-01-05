from __future__ import annotations

import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import mysql.connector
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

from dsutil import LocalLogger

if TYPE_CHECKING:
    from collections.abc import Generator

    from dsbin.wpmusic.wp_config import Config


class DatabaseManager:
    """Manages database connections with MySQL primary and SQLite cache."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = LocalLogger().get_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            simple=self.config.log_simple,
        )

    def _ensure_mysql_tunnel(self) -> None:
        """Ensure MySQL SSH tunnel exists and is working.

        Raises:
            DatabaseError: If the tunnel cannot be established.
        """
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
        """Get MySQL connection through SSH tunnel.

        Yields:
            The database connection.
        """
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
        self,
    ) -> Generator[
        sqlite3.Connection | MySQLConnectionAbstract | PooledMySQLConnection, None, None
    ]:
        """Get a connection for reading, using local cache if available.

        Raises:
            DatabaseError: If the database connection fails.

        Yields:
            The database connection.
        """
        if self.config.no_cache:  # If cache is disabled, use MySQL
            self.logger.debug("Cache disabled, using MySQL directly.")
            with self.get_mysql_connection() as conn:
                yield conn
            return

        try:  # Otherwise, use the cache if it exists, or create it if it doesn't
            if not Path(self.config.local_sqlite_db).exists():
                self.logger.info("No local cache found, creating from MySQL.")
                self.refresh_cache()
            else:
                self.logger.debug("Using local SQLite cache.")

            with sqlite3.connect(self.config.local_sqlite_db) as conn:
                yield conn
        except Exception as e:
            msg = f"Failed to connect to MySQL or SQLite database: {e!s}"
            raise DatabaseError(msg) from e

    def check_database(self) -> None:
        """Check database connection and log track and upload counts."""
        with self.get_mysql_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tracks")
            result = cursor.fetchone()
            track_count = result[0] if result else 0

            cursor.execute("SELECT COUNT(*) FROM uploads")
            result = cursor.fetchone()
            upload_count = result[0] if result else 0

            self.logger.info(
                "Database connection successful! Found %s tracks and %s uploads.",
                track_count,
                upload_count,
            )

    def force_db_refresh(self, force_refresh: bool = False, refresh_only: bool = False) -> bool:
        """Force a refresh of the local cache from MySQL."""
        if force_refresh:
            self.logger.info("Forcing cache refresh from MySQL server...")
            self.force_refresh()
            self.logger.info("Cache refresh complete!")
            if refresh_only:
                return True
        return False

    def record_upload_set_to_db(self, uploaded: str, current_upload_set: dict) -> None:
        """Record the current upload set to the database.

        Raises:
            DatabaseError: If the database operation fails.
        """
        with self.get_mysql_connection() as conn:
            cursor = conn.cursor()
            for track_name, audio_tracks in current_upload_set.items():
                cursor.execute("INSERT IGNORE INTO tracks (name) VALUES (%s)", (track_name,))
                cursor.execute("SELECT id FROM tracks WHERE name = %s", (track_name,))
                result = cursor.fetchone()
                if not result:
                    msg = f"Failed to get track ID for {track_name}"
                    raise DatabaseError(msg)

                track_id = result[0]

                for track in audio_tracks.values():
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM uploads
                        WHERE track_id = %s AND filename = %s AND instrumental = %s AND uploaded = %s
                        """,
                        (track_id, track.filename, track.is_instrumental, uploaded),
                    )

                    result = cursor.fetchone()
                    if result and result[0] == 0:
                        cursor.execute(
                            """
                            INSERT INTO uploads (track_id, filename, instrumental, uploaded)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (track_id, track.filename, track.is_instrumental, uploaded),
                        )

            conn.commit()

            # Refresh the local cache after successful write
            self.refresh_cache()

    def get_upload_history(self, track_name: str | None = None) -> list[dict]:
        """Retrieve upload history from local cache, optionally filtered by track name."""
        if self.config.no_cache:
            self.logger.debug("Retrieving upload history from MySQL.")
        else:
            self.logger.debug("Retrieving upload history from local cache.")

        history = []
        with self.get_read_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                conn.row_factory = sqlite3.Row
                param_placeholder = "?"
                case_insensitive_func = "LOWER"
            else:
                param_placeholder = "%s"
                case_insensitive_func = "LOWER"

            cursor = (
                conn.cursor(dictionary=True)
                if isinstance(conn, MySQLConnectionAbstract | PooledMySQLConnection)
                else conn.cursor()
            )

            if track_name:
                cursor.execute(
                    f"""
                    SELECT t.name as track_name, u.filename, u.instrumental, u.uploaded
                    FROM tracks t
                    JOIN uploads u ON t.id = u.track_id
                    WHERE {case_insensitive_func}(t.name) = {case_insensitive_func}({param_placeholder})
                    ORDER BY u.uploaded DESC
                    """,
                    (track_name,),
                )
            else:
                cursor.execute("""
                    SELECT t.name as track_name, u.filename, u.instrumental, u.uploaded
                    FROM tracks t
                    JOIN uploads u ON t.id = u.track_id
                    ORDER BY t.name, u.uploaded DESC
                    """)

            rows = cursor.fetchall()
            current_track = None
            for row in rows:
                # Handle both SQLite.Row and MySQL dict formats
                row_data = dict(row) if isinstance(conn, sqlite3.Connection) else row

                # Convert datetime to ISO string if it's a datetime object
                uploaded = row_data["uploaded"]
                if isinstance(uploaded, datetime):
                    uploaded = uploaded.isoformat()

                if current_track is None or current_track["track_name"] != row_data["track_name"]:
                    if current_track is not None:
                        history.append(current_track)
                    current_track = {"track_name": row_data["track_name"], "uploads": []}
                current_track["uploads"].append(
                    {
                        "filename": row_data["filename"],
                        "instrumental": row_data["instrumental"],
                        "uploaded": uploaded,
                    }
                )

            if current_track is not None:
                history.append(current_track)

        return history

    def refresh_cache(self) -> None:
        """Refresh the local SQLite cache from MySQL."""
        with (
            self.get_mysql_connection() as mysql_conn,
            sqlite3.connect(self.config.local_sqlite_db) as sqlite_conn,
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
        self.logger.debug("Forcing cache refresh from MySQL.")
        if Path(self.config.local_sqlite_db).exists():
            Path(self.config.local_sqlite_db).unlink()
        self.refresh_cache()

    def is_cache_stale(self) -> bool:
        """Check if local cache needs updating by comparing row counts."""
        self.logger.debug("Forcing cache refresh from MySQL.")
        cache_path = Path(self.config.local_sqlite_db)
        if cache_path.exists():
            cache_path.unlink()
        self.refresh_cache()

        try:
            with self.get_mysql_connection() as mysql_conn:
                mysql_cursor = mysql_conn.cursor()
                mysql_cursor.execute("SELECT COUNT(*) FROM uploads")
                result = mysql_cursor.fetchone()
                mysql_count = result[0] if result else 0

                with sqlite3.connect(self.config.local_sqlite_db) as sqlite_conn:
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

    @staticmethod
    def _init_sqlite_schema(conn: sqlite3.Connection) -> None:
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
