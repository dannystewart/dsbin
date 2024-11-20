from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection

from dsbin.music.wpmusiclib.db_manager import DatabaseError, DatabaseManager
from dsbin.music.wpmusiclib.table_formatter import TableFormatter

from dsutil.log import LocalLogger

if TYPE_CHECKING:
    from .wp_config import Config

tz = ZoneInfo("America/New_York")


class UploadTracker:
    """Track, log, and print file uploads."""

    def __init__(self, config: Config):
        self.config = config
        self.db = DatabaseManager(config)
        self.logger = LocalLogger.setup_logger(self.__class__.__name__, level=self.config.log_level)

        # Track the current set of uploads before recording them to the upload log
        self.current_upload_set = defaultdict(dict)

    def _init_db(self) -> None:
        with sqlite3.connect(self.config.local_sqlite_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    instrumental BOOLEAN NOT NULL,
                    uploaded TIMESTAMP NOT NULL,
                    FOREIGN KEY (track_id) REFERENCES tracks(id)
                )
            """)
            conn.commit()

    def log_upload_set(self) -> None:
        """Log the current set of uploads and clear the set."""
        if not self.current_upload_set:
            return

        # Get current time and format it for MySQL
        uploaded = datetime.now(tz=tz).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_mysql_connection() as conn:
            cursor = conn.cursor()
            for track_name, audio_tracks in self.current_upload_set.items():
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
            self.db.refresh_cache()

        self.current_upload_set.clear()

    def get_upload_history(self, track_name: str | None = None) -> list[dict]:
        """Retrieve upload history from local cache, optionally filtered by track name."""
        if self.config.no_cache:
            self.logger.debug("Retrieving upload history from MySQL.")
        else:
            self.logger.debug("Retrieving upload history from local cache.")

        history = []
        with self.db.get_read_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                conn.row_factory = sqlite3.Row
                param_placeholder = "?"
            else:
                param_placeholder = "%s"

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
                    WHERE t.name = {param_placeholder}
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

    def pretty_print_history(self, track_name: str | None = None) -> None:
        """Print the upload history in a neatly organized way with color."""
        history = self.get_upload_history(track_name)
        table_formatter = TableFormatter(apply_limit=track_name is None)

        for entry in history:
            table_formatter.print_table(entry["uploads"], entry["track_name"])
