from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING

from zoneinfo import ZoneInfo

from dsutil.log import LocalLogger

from .table_formatter import TableFormatter

if TYPE_CHECKING:
    from .wp_config import Config

tz = ZoneInfo("America/New_York")


class UploadTracker:
    """Track, log, and print file uploads."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = LocalLogger.setup_logger(
            self.__class__.__name__,
            level=self.config.log_level,
            message_only=True,
        )
        self.current_upload_set = defaultdict(dict)

    def _init_db(self) -> None:
        with sqlite3.connect(self.config.upload_log_db) as conn:
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

        uploaded = datetime.now(tz=tz).isoformat()

        with sqlite3.connect(self.config.upload_log_db) as conn:
            cursor = conn.cursor()
            for track_name, audio_tracks in self.current_upload_set.items():
                cursor.execute("INSERT OR IGNORE INTO tracks (name) VALUES (?)", (track_name,))
                cursor.execute("SELECT id FROM tracks WHERE name = ?", (track_name,))
                track_id = cursor.fetchone()[0]

                # Check if an identical entry already exists
                for track in audio_tracks.values():
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM uploads
                        WHERE track_id = ? AND filename = ? AND instrumental = ? AND uploaded = ?
                    """,
                        (track_id, track.filename, track.is_instrumental, uploaded),
                    )

                    # If no identical entry exists, insert the new one
                    if cursor.fetchone()[0] == 0:
                        cursor.execute(
                            """
                            INSERT INTO uploads (track_id, filename, instrumental, uploaded)
                            VALUES (?, ?, ?, ?)
                        """,
                            (track_id, track.filename, track.is_instrumental, uploaded),
                        )

            conn.commit()

        self.current_upload_set.clear()

    def get_upload_history(self, track_name: str = None) -> list[dict]:
        """Retrieve upload history, optionally filtered by track name."""
        history = []
        with sqlite3.connect(self.config.upload_log_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if track_name:
                cursor.execute(
                    """
                    SELECT t.name as track_name, u.filename, u.instrumental, u.uploaded
                    FROM tracks t
                    JOIN uploads u ON t.id = u.track_id
                    WHERE t.name = ?
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
                if current_track is None or current_track["track_name"] != row["track_name"]:
                    if current_track is not None:
                        history.append(current_track)
                    current_track = {"track_name": row["track_name"], "uploads": []}
                current_track["uploads"].append({
                    "filename": row["filename"],
                    "instrumental": row["instrumental"],
                    "uploaded": row["uploaded"],
                })
            if current_track is not None:
                history.append(current_track)

        return history

    def pretty_print_history(self, track_name: str | None = None, limit: int | None = 10) -> None:
        """Print the upload history in a neatly organized way with color."""
        history = self.get_upload_history(track_name)
        table_formatter = TableFormatter()

        for entry in history:
            table_formatter.print_table(entry["uploads"], entry["track_name"], limit)
