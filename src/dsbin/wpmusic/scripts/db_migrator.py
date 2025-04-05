from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING

import mysql.connector
from polykit.log import Logician

from dsbin.wpmusic.configs import WPConfig

if TYPE_CHECKING:
    from collections.abc import Generator

logger = Logician.get_logger()


def run(command: str) -> tuple[bool, str]:
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


def ensure_ssh_tunnel(port: int, service_name: str = "SSH tunnel", kill: bool = False) -> None:
    """Check for an SSH tunnel on a specified port and establish one if needed."""
    logger.info("Checking for existing %s on port %s...", service_name, port)
    kill_existing_ssh_tunnel(service_name, port, kill)
    establish_ssh_tunnel(port, service_name)


def kill_existing_ssh_tunnel(service_name: str, port: int, kill: bool) -> None:
    """Kill an existing SSH tunnel."""
    success, output = run(f"lsof -ti:{port} -sTCP:LISTEN")
    if success and output.strip():
        ssh_tunnel_pid = output.strip()
        logger.info("Found existing %s with PID: %s. Killing...", service_name, ssh_tunnel_pid)
        run(f"kill -9 {ssh_tunnel_pid}")
        logger.info("Existing %s killed.", service_name)
    else:
        logger.info("No existing %s found. Starting now...", service_name)
        if kill:
            return


def establish_ssh_tunnel(port: int, service_name: str) -> None:
    """Establish an SSH tunnel to a remote server."""
    success, _ = run(f"ssh -fNL {port}:localhost:{port} danny@web")
    if success:
        logger.info("%s established.", service_name)
    else:
        logger.error("Failed to establish SSH tunnel. Exiting...")


@contextmanager
def create_tunnel() -> Generator[None, None, None]:
    """Create and manage SSH tunnel lifecycle."""
    try:
        ensure_ssh_tunnel(3306, "MySQL SSH tunnel")
        yield
    finally:
        kill_existing_ssh_tunnel("MySQL SSH tunnel", 3306, kill=True)


def test_mysql_credentials(config: WPConfig) -> bool:
    """Test MySQL credentials directly on the server."""
    try:
        cmd = (
            f"ssh {config.ssh_user}@{config.ssh_host} "
            f"'mysql -u{config.db_user} -p{config.db_password} "
            f'-h127.0.0.1 {config.db_name} -e "SELECT 1"\''
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        logger.debug("MySQL direct connection test result:\n%s", result.stdout)
        return result.returncode == 0
    except Exception as e:
        logger.error("Failed to test MySQL credentials: %s", str(e))
        return False


def migrate_data(config: WPConfig) -> None:
    """Migrate data from SQLite to MySQL."""
    sqlite_conn = sqlite3.connect(config.local_sqlite_db)

    try:
        with create_tunnel():
            mysql_conn = mysql.connector.connect(
                host="localhost",
                database=config.db_name,
                user="root",
                password="sCgTqivNGnKUw93easv4tyxa",
                collation="utf8mb3_general_ci",
                charset="utf8mb3",
            )

            try:
                # First migrate tracks
                logger.info("Migrating tracks...")
                sqlite_cursor = sqlite_conn.cursor()
                mysql_cursor = mysql_conn.cursor()

                sqlite_cursor.execute("SELECT id, name FROM tracks")
                tracks = sqlite_cursor.fetchall()

                for track in tracks:
                    mysql_cursor.execute("INSERT INTO tracks (id, name) VALUES (%s, %s)", track)

                # Migrate uploads with datetime conversion
                logger.info("Migrating uploads...")
                sqlite_cursor.execute(
                    "SELECT id, track_id, filename, instrumental, uploaded FROM uploads"
                )
                uploads = sqlite_cursor.fetchall()

                for upload in uploads:
                    # Convert the datetime string
                    db_id, track_id, filename, instrumental, uploaded_str = upload
                    uploaded_dt = datetime.fromisoformat(uploaded_str)
                    mysql_upload = (db_id, track_id, filename, instrumental, uploaded_dt)

                    mysql_cursor.execute(
                        """
                        INSERT INTO uploads
                        (id, track_id, filename, instrumental, uploaded)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        mysql_upload,
                    )

                # Commit the changes
                mysql_conn.commit()
                logger.info("Migration completed successfully!")

                # Get and print some stats
                mysql_cursor.execute("SELECT COUNT(*) FROM tracks")
                result = mysql_cursor.fetchone()
                track_count = result or 0

                mysql_cursor.execute("SELECT COUNT(*) FROM uploads")
                result = mysql_cursor.fetchone()
                upload_count = result or 0

                logger.info("Migrated %s tracks and %s uploads.", track_count, upload_count)

            finally:
                mysql_conn.close()
    finally:
        sqlite_conn.close()


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Database migration and connection testing utility"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only test the database connection without migrating",
    )
    args = parser.parse_args()

    try:
        config = WPConfig(skip_upload=True, keep_files=True)

        if args.test_only:
            with create_tunnel():
                mysql_conn = mysql.connector.connect(
                    host="localhost",
                    database=config.db_name,
                    user=config.db_user,
                    password=config.db_password,
                    collation="utf8mb3_general_ci",
                    charset="utf8mb3",
                )
                try:
                    cursor = mysql_conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM tracks")
                    result = cursor.fetchone()
                    track_count = result or 0
                    logger.info("Connection successful! Found %s tracks.", track_count)
                finally:
                    mysql_conn.close()
        else:
            logger.warning(
                "This will migrate data. Are you sure? Use --test-only to just test connection."
            )
            response = input("Continue with migration? [y/N] ").lower()
            if response == "y":
                migrate_data(config)
            else:
                logger.info("Migration canceled.")

    except KeyboardInterrupt:
        logger.info("Operation canceled by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Operation failed: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
