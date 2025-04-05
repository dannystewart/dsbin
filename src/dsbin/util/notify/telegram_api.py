"""Send Telegram messages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests
from polykit.log import PolyLog

if TYPE_CHECKING:
    from logging import Logger


class TelegramAPIHelper:
    """Helper class to interact with the Telegram API.

    You must supply your own API token as well as your chat ID in order to use the class. It
    provides a call_api method to make a POST request to the Telegram API using the specified
    method, payload, and timeout.

    Attributes:
        token: The token to use for the Telegram Bot API.
        chat_id: The chat ID to use for the Telegram chat.
    """

    def __init__(self, token: str, chat_id: str):
        self.logger: Logger = PolyLog.get_logger()
        self.token: str = token
        self.chat_id: str = chat_id
        self.url: str = f"https://api.telegram.org/bot{self.token}"
        self.timeouts: dict[str, int] = {"sendPhoto": 30, "sendAudio": 60}
        self.default_timeout: int = 10

    def call_api(
        self,
        api_method: str,
        payload: dict[str, str] | None = None,
        timeout: int | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Make a POST request to the Telegram API using the specified method, payload, and timeout.

        If timeout is not specified, it's determined dynamically based on the API method if it's a
        commonly used method, or else the default timeout is used.

        If files are provided, it uses the `data` parameter to properly handle multipart/form-data.
        Otherwise, it defaults to sending the payload as JSON. The payload is filtered to remove any
        None values before sending the request.

        Args:
            api_method: The API method to call.
            payload: The payload to send to the API. Defaults to None.
            timeout: The timeout for the request. If None, the timeout is determined dynamically
                based on the API method if it's a commonly used method, or the default timeout is
                used. Defaults to None.
            files: A dictionary for multipart encoding upload. Defaults to None.
                Examples: `{"param_name": file-tuple}`, `{"param_name": file-like-object}`

        Returns:
            The response data in JSON if the request is successful.

        Raises:
            Exception: If the request to the Telegram API fails.
        """
        url = f"{self.url}/{api_method}"
        payload = dict(payload.items()) if payload else {}
        timeout = timeout or self.timeouts.get(api_method, self.default_timeout)

        try:
            response = (
                requests.post(url, data=payload, files=files, timeout=timeout)
                if files
                else requests.post(url, json=payload, timeout=timeout)
            )
            response_data = response.json()
            if not response_data.get("ok"):
                error_msg = response_data.get("description", "Unknown error.")
                self.logger.error("Failed to call %s: %s", api_method, error_msg)
                self.logger.debug("Code %s: %s", response.status_code, response_data)
                msg = f"Failed to call {api_method}: {error_msg}"
                raise Exception(msg)
            return response_data
        except requests.RequestException as e:
            self.logger.warning("Request to Telegram API failed: %s", str(e))
            msg = f"Request to Telegram API failed: {e}"
            raise Exception(msg) from e
