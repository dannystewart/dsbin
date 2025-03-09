# ruff: noqa: DTZ005

from __future__ import annotations

import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TRUNC_LENGTH = 30


def get_filename() -> str:
    """Get the filename for the content."""
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    return f"file_{timestamp}.txt"


def create_temp_file(filename: str, content: str) -> Path:
    """Create a temporary text file with the given content."""
    temp_file = Path(tempfile.gettempdir()) / filename
    temp_file.write_text(content)
    return temp_file


def set_file_to_clipboard(file_path: Path) -> None:
    """Set the file to the macOS clipboard using osascript."""
    apple_script = f"""
    set theFile to POSIX file "{file_path}"
    set the clipboard to theFile
    """
    subprocess.run(["osascript", "-e", apple_script], check=True)


def escape_for_applescript(text: str) -> str:
    """Escape text for use in AppleScript string."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")


def format_content(content: str) -> str:
    """Truncate the content for the notification."""
    text = content.replace("\n", " ").strip()
    if len(text) > TRUNC_LENGTH:
        text = text[:TRUNC_LENGTH] + "..."
    return escape_for_applescript(text)


def notify(message: str) -> None:
    """Show a macOS notification."""
    apple_script = f'display notification "{message}" with title "Text to File"'
    subprocess.run(["osascript", "-e", apple_script], check=True)


if __name__ == "__main__":
    content = sys.argv[1]
    filename = get_filename()
    temp_file = create_temp_file(filename, content)
    set_file_to_clipboard(temp_file)

    notify_content = format_content(content)
    notify_string = f"'{notify_content}'\ncopied to temp file on clipboard"
    notify(notify_string)
