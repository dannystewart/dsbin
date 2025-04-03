"""macOS-specific functions and utilities."""

from __future__ import annotations

import subprocess


def macos_notification(
    message: str, title: str, subtitle: str | None = None, sound: bool = False
) -> None:
    """Display a macOS system notification using osascript.

    Args:
        message: The main notification message.
        title: The notification title.
        subtitle: An optional subtitle for the notification.
        sound: Whether to play the default notification sound. Defaults to False.

    Raises:
        subprocess.CalledProcessError: If the osascript command fails.
    """
    script_parts = ["display notification", f'"{message}"', f'with title "{title}"']

    if subtitle:
        script_parts.append(f'subtitle "{subtitle}"')

    if sound:
        script_parts.append('sound name "default"')

    script = " ".join(script_parts)

    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise
