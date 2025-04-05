"""Send emails using an SMTP server configured via environment variables."""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

from polykit.log import Logician


class MailSender:
    """Send emails over SMTP. Credentials must be provided.

    Attributes:
        name: The name to use for the sender of the email.
        email: The email address to send emails from.
        smtp_server: The SMTP server to use.
        smtp_port: The port to use for the SMTP server.
        smtp_user: The username to use for the SMTP server.
        smtp_password: The password to use for the SMTP server.
        timeout: The timeout to use for the SMTP connection. Defaults to 10 seconds.
    """

    def __init__(
        self,
        name: str,
        email: str,
        smtp_server: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        timeout: int = 10,
    ):
        self.logger = Logician.get_logger(f"{self.__class__.__name__}")
        self.name = name
        self.email = email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.timeout = timeout

    def send_email(
        self, subject: str, body: str, recipients: str | list[str] | None = None
    ) -> bool:
        """Compose and prepare an email with the given subject and body, then send it using
        the configured SMTP server.

        Args:
            subject: The subject of the email.
            body: The body of the email.
            recipients: A list of email addresses to send the email to. If no recipients are
                provided, the email will be sent to the sender's address.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        if recipients is None:
            recipients = [self.email]
        elif isinstance(recipients, str):
            recipients = [recipients]

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.email
        msg["To"] = ", ".join(recipients) if recipients else self.email

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as server:
                return self.handle_send(server, msg, recipients)
        except smtplib.SMTPException as e:
            print(f"SMTP error occurred: {e}")
            return False

    def handle_send(self, server: smtplib.SMTP, msg: MIMEText, recipients: list[str]) -> bool:
        """Send an email message using the provided SMTP server.

        Args:
            server: The SMTP server to use.
            msg: The email message to send.
            recipients: A list of email addresses to send the email to.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        try:
            return self._connect_and_send(server, recipients, msg)
        except smtplib.SMTPException as e:
            self.logger.error("SMTP error occurred: %s", str(e))
        except Exception as e:
            self.logger.exception("Failed to send email: %s", str(e))
        return False

    def _connect_and_send(self, server: smtplib.SMTP, recipients: list[str], msg: MIMEText) -> bool:
        """Connect to the SMTP server and send an email message."""
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self.smtp_user, self.smtp_password)
        to_addrs = recipients or self.email
        server.send_message(msg, to_addrs=to_addrs)
        self.logger.info("Email sent successfully.")
        return True
