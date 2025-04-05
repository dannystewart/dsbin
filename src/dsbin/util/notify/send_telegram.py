"""Send Telegram messages."""

from __future__ import annotations

from pathlib import Path

import requests
from polykit.log import Logician

from .telegram_api import TelegramAPIHelper


class TelegramSender:
    """Send messages to a Telegram chat.

    You must supply your own API token as well as your chat ID in order to use the class. It
    provides a send_message method to send a message to the chat.

    Attributes:
        token: The token to use for the Telegram Bot API.
        chat_id: The chat ID to use for the Telegram chat.
    """

    def __init__(self, token: str, chat_id: str):
        self.logger = Logician.get_logger()
        self.api = TelegramAPIHelper(token, chat_id)
        self.chat_id = chat_id

    def send_message(
        self,
        message: str,
        chat_id: str | None = None,
        parse_mode: str | None = None,
        log: bool = False,
    ) -> bool:
        """Send a message to a Telegram chat.

        Uses the chat ID and token provided during initialization of the class.

        Args:
            message: The message to send.
            chat_id: The chat ID to send the message to if you want to override what the class
                instance uses. Defaults to None.
            parse_mode: The parse mode to use for message formatting. Supports "Markdown",
                "MarkdownV2", or "HTML". Defaults to None, in which case parse_mode won't be
                included in the payload at all.
            log: Whether to log a successful send. Defaults to False.

        Returns:
            True if the message was sent successfully, False if the message failed to send.
        """
        payload = {"chat_id": chat_id or self.chat_id, "text": message}

        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            self.api.call_api("sendMessage", payload)
            if log:
                self.logger.info("Telegram message sent successfully.")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error("Failed to send message to Telegram: %s", str(e))
            return False

    def send_audio_file(
        self,
        audio_path: str,
        chat_id: str | None = None,
        caption: str | None = None,
        duration: int | None = None,
        title: str | None = None,
        performer: str | None = None,
    ) -> bool:
        """Send a local audio file to a specified chat.

        Supports optional message modification and deletion by providing a message ID and new text.
        Optionally remove an attached keyboard after modification.

        Args:
            audio_path: The path of the local audio file to send.
            chat_id: The chat ID to send the message to if you want to override what
                the class instance uses. Defaults to None.
            caption: The new text to replace the message with, if applicable.
            duration: Duration of the audio in seconds.
            title: Title of the audio.
            performer: Name of the performer (displayed under the title).
        """
        try:
            with Path(audio_path).open(encoding="utf-8") as audio_file:
                payload = {
                    "chat_id": str(chat_id) or str(self.chat_id),
                    "duration": str(duration),
                    "title": str(title),
                    "performer": str(performer),
                    "caption": str(caption),
                }
                self.api.call_api("sendAudio", payload, files={"audio": audio_file})
            return True
        except Exception as e:
            self.logger.error("Failed to send audio file: %s", str(e))
            return False
