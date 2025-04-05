from __future__ import annotations

import sqlite3
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import mysql.connector
from polykit.log import Logician

from dsbin.util.db import MySQLHelper, SQLiteHelper

if TYPE_CHECKING:
    from collections.abc import Generator

    from mysql.connector.abstracts import MySQLConnectionAbstract
    from mysql.connector.pooling import PooledMySQLConnection

    from dsbin.wpmusic.configs import WPConfig


class DatabaseManager:
    """Manages database connections with MySQL primary and SQLite cache."""

    def __init__(self, config: WPConfig):
        self.config = config
        self.logger = Logician.get_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            simple=self.config.log_simple,
        )
        self.mysql = MySQLHelper(
            host=self.config.db_host,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password,
        )
        self.sqlite = SQLiteHelper(self.config.local_sqlite_db)

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
            )
            yield conn
        finally:
            if "conn" in locals():
                conn.close()

    def get_read_connection(self) -> MySQLHelper | SQLiteHelper:
        """Get a connection for reading, using local cache if available."""
        if self.config.no_cache:
            self._ensure_mysql_tunnel()
            self.logger.debug("Cache disabled, using MySQL directly.")
            return self.mysql

        if not Path(self.config.local_sqlite_db).exists():
            self.logger.info("No local cache found, creating from MySQL.")
            self.refresh_cache()
        else:
            self.logger.debug("Using local SQLite cache.")
        return self.sqlite

    def check_database(self) -> None:
        """Check database connection and log track and upload counts."""
        self._ensure_mysql_tunnel()

        track_count = self.mysql.fetch_one("SELECT COUNT(*) as count FROM tracks")["count"]
        upload_count = self.mysql.fetch_one("SELECT COUNT(*) as count FROM uploads")["count"]

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

    def record_upload_set_to_db(self, uploaded: str, current_upload_set: dict[str, Any]) -> None:
        """Record the current upload set to the database."""
        self._ensure_mysql_tunnel()

        conn = self.mysql.pool.get_connection()
        try:
            cursor = conn.cursor()
            for track_name, audio_tracks in current_upload_set.items():
                cursor.execute("INSERT IGNORE INTO tracks (name) VALUES (%s)", (track_name,))
                cursor.execute("SELECT id FROM tracks WHERE name = %s", (track_name,))
                result = cursor.fetchone()
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
        finally:
            conn.close()

        # Refresh cache after successful write
        self.refresh_cache()

    def get_upload_history(self, track_name: str | None = None) -> list[dict[str, Any]]:
        """Retrieve upload history from local cache, optionally filtered by track name."""
        if self.config.no_cache:
            self.logger.debug("Retrieving upload history from MySQL.")
        else:
            self.logger.debug("Retrieving upload history from local cache.")

        history = []
        db = self.get_read_connection()

        query = """
            SELECT t.name as track_name, u.filename, u.instrumental, u.uploaded
            FROM tracks t
            JOIN uploads u ON t.id = u.track_id
        """

        if track_name:
            query += (
                " WHERE LOWER(t.name) = LOWER(?)"
                if isinstance(db, SQLiteHelper)
                else " WHERE LOWER(t.name) = LOWER(%s)"
            )
            query += " ORDER BY u.uploaded DESC"
            results = db.fetch_many(query, (track_name,))
        else:
            query += " ORDER BY t.name, u.uploaded DESC"
            results = db.fetch_many(query)

        # Process results into the required format
        history = []
        current_track = None

        for row in results:
            if current_track is None or current_track["track_name"] != row["track_name"]:
                if current_track is not None:
                    history.append(current_track)
                current_track = {"track_name": row["track_name"], "uploads": []}

            uploaded = row["uploaded"]
            if isinstance(uploaded, datetime):
                uploaded = uploaded.isoformat()

            current_track["uploads"].append({
                "filename": row["filename"],
                "instrumental": row["instrumental"],
                "uploaded": uploaded,
            })

        if current_track is not None:
            history.append(current_track)

        return history

    def refresh_cache(self) -> None:
        """Refresh the local SQLite cache from MySQL."""
        self._ensure_mysql_tunnel()

        # Initialize schema
        self.sqlite.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        """)
        self.sqlite.execute("""
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY,
                track_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                instrumental BOOLEAN NOT NULL,
                uploaded TIMESTAMP NOT NULL,
                FOREIGN KEY (track_id) REFERENCES tracks(id)
            )
        """)

        # Copy data
        tracks = self.mysql.fetch_many("SELECT * FROM tracks")
        for track in tracks:
            self.sqlite.execute(
                "INSERT OR REPLACE INTO tracks (id, name) VALUES (?, ?)",
                (track["id"], track["name"]),
            )

        uploads = self.mysql.fetch_many("SELECT * FROM uploads")
        for upload in uploads:
            self.sqlite.execute(
                "INSERT OR REPLACE INTO uploads (id, track_id, filename, instrumental, uploaded) VALUES (?, ?, ?, ?, ?)",
                (
                    upload["id"],
                    upload["track_id"],
                    upload["filename"],
                    upload["instrumental"],
                    upload["uploaded"],
                ),
            )

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
                res = mysql_cursor.fetchone()
                mysql_count = self._get_result_count(res)

                with sqlite3.connect(self.config.local_sqlite_db) as sqlite_conn:
                    sqlite_cursor = sqlite_conn.cursor()
                    sqlite_cursor.execute("SELECT COUNT(*) FROM uploads")
                    res = sqlite_cursor.fetchone()
                    sqlite_count = self._get_result_count(res)

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
    def _get_result_count(result: Any) -> int:
        """Get the count from a database result."""
        return result[0] if result and isinstance(result, tuple | list) and len(result) > 0 else 0

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
